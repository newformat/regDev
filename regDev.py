'''
скрипт работы формирования скрипта на REXX
"ZigBee присоединение незарег. устройств"
Берет список скрипта с regDevice и список leaveTimeSet. После формирует в файле поочередно.
'''


import csv
import os
import getpass
import re
import time
from datetime import datetime



class SearchCSVFile:

    def __init__(self, search_path, tepl_name):
        self.search_path = search_path  # путь к папке, где хранится csv файл.
        self.tepl_name = tepl_name  # шаблон названия файла

    # TODO: == реализовать отдельный метод провеки пути к файлу здесь ==

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
    '''
     Работа с файлом - запись данных в списки
      TODO:27.11.19 - идея, после переофрмления кода в ООП перевести списки в словарь, так будет лучше, пример:
          list_regDevice =  {'МАС адреса сетей':[...список МАС сетей...], 'МАС адреса устройств':[... список МАС устройств...]
          29.11.19 - дополнение к идеи, формировать список структурно - 1 сеть - его мак адреса, другая сеть - другие мак адреса
    '''

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
    def __init__(self, list_unregDevice):
        self.list_unregDevice = list_unregDevice
        self.list_reg_dev = list()
        self.list_leave_dev = list()
        self.save_file = '' # путь для сохранения файла rzx


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
        mac_networks = ".\\data\\mac_net_big_project.txt"
        mac_list = list()

        with open(mac_networks, "r") as mac_addr:
            for mac in mac_addr:
                mac_list.append(mac.split('\n')[0])

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
            self.save_file = save_path + name_file_zrx
        else:
            self.print_folder_not_found()
            return -1


    def get_template(self, path_template ):
        if (os.path.exists(path_template)):
            with open(path_template, 'r') as template:
                return template.read()


    def file_write(self):
        ''' запись шаблона в файл '''
        template_head = ".\\templates\\header.txt"
        template_footer = ".\\templates\\footer.txt"

        try:

            with open(self.save_file, 'w') as result:
                ''' шапка скрипта '''
                result.write(self.get_template(template_head))

                for count in range(0, len(self.list_reg_dev) - 1):
                    result.write(self.list_reg_dev[count] + '\n')
                    result.write(self.list_leave_dev[count] + '\n')

                result.write(self.get_template(template_footer))
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
    def __init__(self, path_file_csv, list_unregDevice):
        ''' Дата и время создания файла (коректный формат) '''
        self.stat = os.stat(path_file_csv)  # путь к файлу (для даты)
        self.f_str_date = str(datetime.fromtimestamp(self.stat.st_atime).date()) # "Дата"
        self.f_str_time = str(datetime.fromtimestamp(self.stat.st_atime).time()).split(".")[0] # "Время"
        self.statics_unreg_file = r".\monitoring\staticUnregDev.htm"  # путь к статистике файла
        self.count_devices = str(len(list_unregDevice))  # кол-во МАС адресов из списка

    

    def file_write_statics(self):
        ''' запись статистики по файлу '''
        css_font = "<span style=\"font-size:17px; font-family:Verdana\">-&emsp;"
        with open(self.statics_unreg_file, 'a') as statics:
            statics.write(
                css_font + self.f_str_date + "&emsp;   " + self.f_str_time + "&emsp;   " + str(
                    self.count_devices) + "</span><br />\n")
            statics.close()
