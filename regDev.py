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
        self.path_file_csv = search_new_file  # путь к новому csv файлу для работы / search_new_file находится в классе SearchCSVFile
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

    def __init__(self, save_file, name_file_zrx, timer, list_regDevice, list_leaveTimeSet):
        self.save_file = save_file + name_file_zrx  # путь сохранения файла + имя_файла.zrx
        self.Timer = timer  # таймер скрипта для уведомления, что пора обновлять скрипт
        self.list_regDevice = list_regDevice  # список шаблонов с адресами под регистрацию
        self.list_leaveTimeSet = list_leaveTimeSet  # список шаблонов с адресами под время в сети

    def file_write(self):
        try:
            # TODO в перспективах - разделить запись данных - шаблон(начало файла) : список адресов : шаблон(конец файла)
            with open(self.save_file, 'w') as result:
                ''' шапка скрипта '''
                result.write("""CALL ZocSessionTab "SETNAME", -1, "regDev: ["TIME('N')"]";
        CALL TIME('E')
        /********/
""")
                ''' сам скрипт RegDev + LeaveTimeSet '''
                for count in range(0, len(self.list_regDevice) - 1):  # list_regDevice из класса DataWriteForLists
                    result.write(self.list_regDevice[
                                     count] + '\n')  # + list_leaveTimeSet[count] + '\n' (ПОТОМ ВЕРНУТЬ!!!) # list_leaveTimeSet из класса DataWriteForLists)

                # === конец файла, после списка ===
                result.write("run_time = TIME('E')\n")
                result.write("pause_time = " + str(self.Timer) + "\n")
                result.write("if run_time < pause_time then\n")
                result.write("pause_time = (pause_time - run_time)/60\n")
                result.write("do i = 1 to pause_time\n")
                result.write("tab_time = pause_time-i\n")
                result.write("CALL ZocSessionTab \"SETNAME\", -1, \"regDev: timer[\"tab_time%1\" min.]\"\n")
                result.write("delay 60\n")
                result.write("end\n")
                result.write("CALL ZocSessionTab \"SETNAME\", -1, \"regDev: Finished\"\n")
                result.write("CALL ZocSessionTab \"SETBLINKING\", -1, 1")
                result.close()
                # ======== конец файла, конец записи ========

        except FileNotFoundError:
            self.print_file_not_found_error()
            return -1
        except  PermissionError:
            self.print_permission_error()
            return -1

    def print_file_not_found_error(self):
        print('неверно указан путь к папке')

    def print_permission_error(self):
        print('недостаточно прав для создания файла')


class DataAnalysis:
    ''' сбор данных статистики по незарегестрированным устройствам '''
    def __init__(self, path_file_csv, statics_unreg_file, count_devices):
        ''' Дата и время создания файла (коректный формат) '''
        self.stat = os.stat(path_file_csv)  # path_file_csv в DataWriteForLists
        self.f_str_date = str(datetime.fromtimestamp(self.stat.st_atime).date())
        self.f_str_time = str(datetime.fromtimestamp(self.stat.st_atime).time()).split(".")[0]
        self.statics_unreg_file = statics_unreg_file  # r".\monitoring\staticUnregDev.htm"  # путь к статистике файла
        self.count_devices = count_devices  # кол-во МАС адресов из списка

    def file_write_statics(self):
        ''' запись статистики по файлу '''
        css_font = "<span style=\"font-size:17px; font-family:Verdana\">-&emsp;"
        with open(self.statics_unreg_file, 'a') as statics:
            statics.write(
                css_font + self.f_str_date + "&emsp;   " + self.f_str_time + "&emsp;   " + str(
                    self.count_devices) + "</span><br />\n")  # count_devices в DataWriteForLists
            statics.close()
