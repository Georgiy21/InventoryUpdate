import csv
import fnmatch
import os.path
from os import path
from datetime import datetime
from datetimerange import DateTimeRange
from datetime import timedelta

cwd = os.path.dirname(__file__)


class Product:
    def __init__(self):
        pass

    def __repr__(self):
        return "Product('{}', '{}')".format(self.sku, self.stock)

    def __str__(self):
        return "{} - {}".format(self.sku, self.stock)


def get_time_range():
    datemask = '%m-%d-%Y'

    future = datetime.today() + timedelta(days=7)
    fday = datetime.strftime(future, datemask)

    tday = datetime.today().strftime(datemask)
    today = datetime.strptime(tday, datemask)

    time_range = DateTimeRange(tday, fday)


def get_files_list():
    vendor_files = []
    inventory_files = []

    for dirpath, dirnames, files in os.walk(cwd):
        for file_name in files:
            if file_name.endswith('.py'):
                pass
            elif 'export_1.csv' in file_name:
                inventory_files.append(file_name)
            else:
                vendor_files.append(file_name)

    return inventory_files, vendor_files


def main():

    time_range = get_time_range()
    list_of_inv, list_of_ven = get_files_list()

    with open()


if __name__ == '__main__':
    main()
