'''
скрипт работы формирования скрипта на REXX
"ZigBee присоединение незарег. устройств"
Берет список скрипта с regDevice и список leaveTimeSet. После формирует в файле поочередно.
'''


import csv
import os
import getpass
import re
from datetime import datetime
import shutil

class SearchCSVFile:
    ''' поиск файла '''
    def __init__(self, paths):
        self.search_path = paths['search_path']  # путь к папке, где хранится csv файл.
        self.tepl_name = paths['tepl_name']  # шаблон названия файла

    def search_new_file(self):
        ''' находит самый "свежий" файл в каталоге и возвращет его полный путь. '''
        list_paths = list()

        for path in os.listdir(self.search_path):
            if path == self.tepl_name + '.csv' or re.match(self.tepl_name + ' \(\d{0,5}\).csv', path):
                list_paths.append(self.search_path + path)

        if not len(list_paths):
            self.print_not_file()
            input('Нажмите enter чтобы продолжить')
            return -1
        else:
            return max(list_paths, key=os.path.getctime)

    def print_not_file(self):
        print("файла с названием " + self.tepl_name + " не найден")


class DataWriteForLists:
    ''' Работа с файлом - запись данных в списки '''
    def __init__(self, search_new_file):
        self.path_file_csv = search_new_file  # путь к новому csv файлу для работы
        self.list_regDevice = list()


    def chech_path_file(self):
        ''' проверка пути файла '''
        try:
            with open(self.path_file_csv, 'r', newline='') as csv_file:
                self.add_reg_devices(csv.reader(csv_file))  # RegDev список
        except FileNotFoundError:
            self.print_file_not_found()
            return -1


    def add_reg_devices(self, reader):
        ''' RegDev - список '''
        for listReg in reader:
            self.list_regDevice.append(listReg[0].split(';')[0])


    def print_file_not_found(self):
        print('Поиск *.csv файла - неверный путь к файлу')
        input('Нажмите enter чтобы закрыть программу')
        return -1


class DataWriteForFile:
    ''' запись данных в файл .zrx '''
    def __init__(self, list_unregDevice, paths):
        self.list_unregDevice = list_unregDevice
        self.list_reg_dev = list()
        self.list_leave_dev = list()
        self.save_file_zrx = ''
        self.template_head = paths['template_head']
        self.template_footer = paths['template_footer']
        self.mac_networks = paths['mac_networks']

    def formation_template_reg_dev(self):
        ''' формирование шаблона под команду registryDevices '''
        zoc_line = ";CALL ZocSend \"^M\";Call ZocTimeout 8;CALL Zocwait \">\";CALL ZocSend \"^C\";delay 1;"
        for reg_dev in self.list_unregDevice:
            self.list_reg_dev.append(reg_dev + zoc_line)


    def formation_template_leave_dev(self):
        """ формирование шаблона под команду leaveSetTime """
        zoc_leave_command = "CALL ZocSend \"zb.sysopt.leaveTimeSet "
        zoc_leave_time = " 250"
        zoc_leave_time_big = " 720"
        zoc_line = "\";CALL ZocSend \"^M\";Call ZocTimeout 8;CALL Zocwait \">\";CALL ZocSend \"^C\";delay 1;"
        mac_list = list()

        if os.path.exists(mac_networks):
            with open(mac_networks, "r") as mac_addr:
                for mac in mac_addr:
                    mac_list.append(mac.split('\n')[0])
        else:
            input('Warning: mac_net_big_project.txt не найден...')

        for leave_dev in self.list_unregDevice:
            if leave_dev[37:53] in mac_list:
                self.list_leave_dev.append(zoc_leave_command + leave_dev[54:70] + zoc_leave_time_big + zoc_line)
                continue
            self.list_leave_dev.append( zoc_leave_command + leave_dev[54:70] + zoc_leave_time +  zoc_line)


    def get_path(self, save_path, name_file_zrx ):
        """ Получить путь для сохранения файла
        :param save_path - путь к папке
        :param name_file_zrx - название файла
        """
        if os.path.exists(save_path):
            self.save_file_zrx = save_path + name_file_zrx  # путь сохранения файла + имя_файла.zrx
        else:
            self.print_folder_not_found()
            return -1


    def get_template(self, path_template ):
        if (os.path.exists(path_template)):
            with open(path_template, 'r') as template:
                return template.read()


    def file_write(self):
        ''' запись шаблона в файл '''
        try:
            with open(self.save_file_zrx, 'w') as result:
                ''' шапка скрипта '''
                result.write(self.get_template(self.template_head))
                for count in range(0, len(self.list_reg_dev) - 1):
                    result.write(self.list_reg_dev[count] + '\n')
                    result.write(self.list_leave_dev[count] + '\n')
                result.write(self.get_template(self.template_footer))
                result.close()
        except FileNotFoundError:
            self.print_file_not_found_error()
            return -1
        except  PermissionError:
            self.print_permission_error()
            return -1

    def print_file_not_found_error(self):
        print('неверно указан путь к папке')
        input('Нажмите enter чтобы закрыть программу')

    def print_permission_error(self):
        print('недостаточно прав для создания файла')
        input('Нажмите enter чтобы закрыть программу')

    def print_folder_not_found(self):
        print('такой папки нет')
        input('Нажмите enter чтобы закрыть программу')


class DataAnalysis:
    def __init__(self, path_file_csv, list_unregDevice, paths):
        ''' Дата и время создания файла (коректный формат) '''
        ''' пути к файлам '''
        self.stat = os.stat(path_file_csv)  # путь к файлу (для даты)
        self.statics_unreg_file = paths['statics_unreg_file']
        self.template_d_head = paths['template_d_head']
        self.template_d_footer = paths['template_d_footer']
        self.template_head_htm = paths['template_head_htm']
        self.template_footer_htm = paths['template_footer_htm']
        self.path_detail = paths['path_detail']
        self.m_history = paths['m_history']
        ''' дата и время файла csv файла '''
        self.f_str_date = str(datetime.fromtimestamp(self.stat.st_atime).date())
        self.f_str_time = str(datetime.fromtimestamp(self.stat.st_atime).time()).split(".")[0]
        ''' данные - списки и словарь'''
        self.list_unregDevice = list_unregDevice
        self.count_devices = str(len(list_unregDevice))  # кол-во МАС адресов из списка
        self.networks = list() # кол-во МАС адресов сетей и значения
        self.network_devices = dict() # словарь, 'сеть' : [..устройства..]

    def print_error(self, method_name, error_text):
        ''' выход из программы при наличии ошибки '''
        print(f'\nDataAnalysis: method - {method_name}')
        exit(input(f"{error_text}\nclick Enter to exit..."))


    def get_networks_count(self):
        ''' кол-во сетей на незарегистрированные ПУ '''
        for network in self.list_unregDevice:
            if network[37:53] not in self.networks:
                self.networks.append(network[37:53])


    def get_network_devices(self):
        ''' кол-во устройств на каждую сеть
        self.networks - cписок сетей
        self.list_unregDevice - список из *.csv файла
        self.network_devices -  словарь, формат ( сеть - [..устройства этой сети..] )
        temp - список для сохранения устройств одной сети
        :return:
        '''
        for network in self.networks:
            temp = list()
            for network_2 in self.list_unregDevice:
                if network == network_2[37:53]:
                    temp.append(network_2[54:70])
            self.network_devices.update({network : temp})


    def get_template(self, path_template ):
        ''' получить шаблон из файла '''
        if (os.path.exists(path_template)):
            with open(path_template, 'r') as template:
                return template.read()
        self.print_error("get_template", f"ошибка пути - {path_template}")


    def get_data_file(self, path_file):
        ''' возвращает дату последнего изменения файла'''
        if (os.path.exists(path_file)):
            return str(datetime.fromtimestamp(os.stat(path_file).st_mtime).date())
        self.print_error("get_data_file", f"ошибка пути - '{path_file}'")


    def file_write_detail_statics(self):
        ''' подробная статистика по спику файла *.csv
            1. Создать шаблон страницы
            2. Собрать данные для записи
            3. Записать данные в шаблон страницы
            4. Сохранить шаблон с данными в файл в папку detail_stat
            :return:
        '''
        # шаблон шапки + часть таблицы с добавлением даты и времени - head_htm_detail
        head_htm_detail = self.get_template(self.template_d_head)\
            .replace('{data}', self.f_str_date).replace('{time}', self.f_str_time )
        footer_htm_detail = self.get_template(self.template_d_footer)
        # путь записи данных в файл
        path_file_stat = f"{self.path_detail}{self.f_str_date}_{self.f_str_time.replace(':','-')}.htm"

        with open(path_file_stat, 'w') as detail_stat_file:
            detail_stat_file.write(head_htm_detail)
            id = 1
            # список ключей (сетей)
            for network in self.network_devices:
                detail_stat_file.write(f"<tr><td>{id}</td><td>{network}</td><td>{len(self.network_devices[network])}</td>"
                                       f"<td ><input type=\"checkbox\" id=\"hd-{id}\" class=\"hide\"/>"
                                       f"<label for=\"hd-{id}\" >список</label><div>\n")
                for dev in self.network_devices[network]:
                    detail_stat_file.write(f"{dev}\n")
                detail_stat_file.write(f"</div></td></tr>\n")
                id += 1
            detail_stat_file.write(footer_htm_detail)
            detail_stat_file.close()
        # проверка пути
        if os.path.exists(path_file_stat) == False:
            self.print_error('file_write_detail_statics', f"ошибка пути - {path_file_stat}")

        return f".{path_file_stat[12:]}"


    def file_write_statics(self):
        ''' запись статистики в файл [5:7] '''
        month_now = str(datetime.today().date())[5:7]
        year_now = str(datetime.today().date())[:4]
        head_htm = self.get_template(self.template_head_htm)
        footer_htm = self.get_template(self.template_footer_htm)

        # если файл не существует - создать новый
        if os.path.exists(self.statics_unreg_file) == False:
            with open(self.statics_unreg_file, 'w') as write_header:
                write_header.write(head_htm.replace('{MONTH}',month_now).replace('{YEAR}', year_now))
                write_header.close()

        # если новый месяц - архивируем старый файл прошлого месяца в ./history и создаем новый
        if month_now != self.get_data_file(self.statics_unreg_file)[5:7]:
            with open(self.statics_unreg_file, 'a') as write_footer:
                write_footer.write(footer_htm)
                write_footer.close()

            # перемещение файла в папку history в формате "дата.htm"
            shutil.move(self.statics_unreg_file, f"{self.m_history}x."
                                                 f"{self.get_data_file(self.statics_unreg_file)[5:7]}."
                                                 f"{self.get_data_file(self.statics_unreg_file)[:4]}.htm")

            # создание нового файла и запись шапки
            with open(self.statics_unreg_file, 'w') as write_header:
                write_header.write(head_htm.replace('{MONTH}',month_now).replace('{YEAR}', year_now))
                write_header.close()

        # проверка числа, для создания пробела в поле таблицы
        elif str(datetime.today().date())[-2:] != self.get_data_file(self.statics_unreg_file)[-2:]:
            template_gap = "<tr style=\"background-color: #ffe2c0\"><td></td><td></td><td></td><td></td><td></td></tr>"
            with open(self.statics_unreg_file, 'w') as write_header:
                write_header.write(template_gap)
                write_header.close()

        # статистика в деталях
        detail_path_stat = self.file_write_detail_statics()

        # стандартная процедура записи статистики работы скрипта
        with open(self.statics_unreg_file, 'a') as statics:
            statics.write(f"\n<tr><td>{self.f_str_date}</td>")
            statics.write(f"<td>{self.f_str_time}</td>")
            statics.write(f"<td>{len(self.networks)}</td>")
            statics.write(f"<td>{self.count_devices}</td>")
            statics.write(f"<td><a href=\"{detail_path_stat}\">link</a></td></tr>")
            statics.close()


''' список путей для настройки скрипта '''
list_of_paths = {
    'search_csv_file':
        {
            "search_path" : "C:\\Users\\" + getpass.getuser() + "\Downloads\\",
            "tepl_name"   : "attach-unregistered-device-events"
        },

    'data_write_for_file':
        {
            "save_file_zrx"     : "C:\\Users\\" + getpass.getuser() + "\\Desktop\\Основная информация\\REXX\\",
            "save_file_name"    : "registryDevice.zrx",
            "template_head"     : ".\\templates\\rexx\\header.txt",
            "template_footer"   : ".\\templates\\rexx\\footer.txt",
            "mac_networks"      : ".\\data\\mac_net_big_project.txt"
        },

    'data_analysis':
        {
            'template_d_head'     : ".\\templates\\html\\head_detail_stat.txt",
            "template_d_footer"   : ".\\templates\\html\\footer_detail_stat.txt",
            "template_head_htm"   : ".\\templates\\html\\head_statics.txt",
            "template_footer_htm" : ".\\templates\\html\\footer_statics.txt",
            "statics_unreg_file"  : ".\\monitoring\\statistics.htm",
            "path_detail"         : ".\\monitoring\\detail_stat\\",
            "m_history"           : ".\\monitoring\\history\\"
        }
}