import csv
import fnmatch
import os.path
from os import path
from datetime import datetime
from datetimerange import DateTimeRange
from datetime import timedelta

cwd = os.path.dirname(__file__)


inventory_fields = ["Handle", "Title", "Option1 Name", "Option1 Value",	"Option2 Name",	"Option2 Value",
                    "Option3 Name", "Option3 Value", "SKU", "HS Code", "COO", "Wholesale Furniture Brokers"]


class InventoryProduct:

    def __init__(self, sku, qty):
        self.sku = sku
        self.qty = qty

    def __repr__(self):
        return "Product('{}', '{}')".format(self.sku, self.qty)

    def __str__(self):
        return "{} - {}".format(self.sku, self.qty)


class Product:

    def __init__(self, line, vendor):
        self.line = line
        self.vendor = vendor.split()[0].lower()
        self.sku = sku()

    def get_timerange(self):

        if self.vendor == 'brassex':
            datemask = '%Y-%m-%d'
        else:
            datemask = '%m-%d-%Y'

        future_date = datetime.today() + timedelta(days=7)
        today_date = datetime.today()

        fday = datetime.strftime(future_date, datemask)
        tday = datetime.strftime(today_date, datemask)

        time_range = DateTimeRange(tday, fday)

        return time_range

    @property
    def sku(self):
        for k, v in self.line.items():
            # not tested
            if 'bestar' in self.vendor.lower() and (k == 'ITEM' or k == 'ï»¿ITEM'):
                self.sku = v
            # not tested
            elif 'we' in self.vendor.lower() and k == 'SKU':
                self.sku = v
            # not tested
            elif 'brassex' in self.vendor.lower() and k == 'SKU':
                self.sku = v
            # not tested
            elif 'zuo modern' in self.vendor.lower() and k == 'ITEN NO':
                self.sku = v
            # not tested
            elif 'mobital' in self.vendor.lower() and k == 'ItemNumber':
                self.sku = v.replace('-', '').strip()
            # not tested
            elif 'mlily' in self.vendor.lower() and k == 'SKU' and v != '':
                self.sku = v
            elif 'night&day' in self.vendor.lower():
                pass
            elif 'primo' in self.vendor.lower():
                pass

        return self.sku

    @property
    def qty(self):
        for k, v in self.line.items():
            # not tested
            if 'bestar' in self.vendor:
                time_range = get_timerange()
                if k == 'NEXT DATE' and v != '':
                    if v in time_range:
                        self.qty = line['QTY'] + line['NEXT QTY']
                break
            # not tested
            elif 'we' in self.vendor and k == 'Stock':
                self.qty = v
                break
            # not tested
            elif 'brassex' in self.vendor:
                time_range = get_timerange()
                if k == 'ETA DATE' and v != '':
                    if v in time_range:
                        self.qty = k['AVAILABLE QTY'] + k['IN-TRANSIT QTY']
                break
            # not tested
            elif 'zuo modern' in self.vendor and k == 'QTY':
                self.qty = v
                break
            # not tested
            elif 'mobital' in self.vendor and k == 'Quantity on Hand':
                self.qty = v
                break
            # not tested
            elif 'mlily' in self.vendor and k == 'Inventory' and v != '':
                self.qty = v
                break
            elif 'night&day' in self.vendor:
                pass
            elif 'primo' in self.vendor:
                pass

        return self.qty

    def __repr__(self):
        return "Product('{}', '{}')".format(self.sku, self.qty)

    def __str__(self):
        return "{} - {}".format(self.sku, self.qty)


def get_files_list():

    inv_ven_dict = dict()
    ven_list = []
    inv_list = []

    for dirpath, dirnames, files in os.walk(cwd):
        for file_name in files:
            if file_name.endswith('.py'):
                pass
            elif 'export_1.csv' in file_name:
                inv_list.append(file_name)
            elif file_name.endswith('.csv'):
                ven_list.append(file_name)

    for v in ven_list:
        v_name = v.split()[0]
        for i in inv_list:
            if v_name.lower() in i.lower():
                inv_ven_dict[i] = v

    return inv_ven_dict

# not tested


def remove_first_line(inp_file):
    reader = csv.DictReader(inp_file)

    with open(inp_file, 'w', newline='') as new_file_1:
        writer = csv.writer(new_file_1)

        writer.writerow(reader[1:])

    new_file_1.close()


def update_inventory(inv_list, ven_list):
    result = dict()

    for i_p in inv_list:
        for v_p in inv_list:
            if i_p.sku == v_p.sku:
                result[i_p.qty] = v_p.qty

    # discontinued
    for p in inv_list:
        if p.sku not in result.keys():
            result[p.qty] = '-50'

    return result


def gen_updated_file(inventory_reader, values):
    with open('updated_inventory.csv', 'w', newline='', encoding='utf8') as updated_file:
        writer = csv.DictWriter(updated_file, fieldnames=inventory_fields)
        for line in inventory_reader:
            for k, v in values.items():
                if k == line['SKU']:
                    line.update({'Wholesale Furniture Brokers': v})
            writer.writerow(line)

    updated_file.close()
    print('UPDATED FILE IS PRINTED')


def main():

    inv_ven_dict = get_files_list()

    for inventory, vendor in inv_ven_dict.items():

        # time_range = get_time_range(vendor)

        inv_products = []
        ven_products = []

        with open(inventory, 'r', encoding='utf8') as inventory_file:
            inventory_reader = csv.DictReader(inventory_file)

            for line in inventory_reader:
                product = InventoryProduct(
                    line['SKU'], line['Wholesale Furniture Brokers'])
                inv_products.append(product)

            with open(vendor, 'r', encoding='utf8') as vendor_file:

                # not tested
                if 'brassex' in vendor.lower():
                    vendor_file = remove_first_line(vendor_file)

                vendor_reader = csv.DictReader(vendor_file)

                for line in inventory_reader:
                    product = Product(line, vendor)
                    ven_products.append(product)

                result = update_inventory(inv_products, ven_products)

                inventory_file.seek(0)

                gen_updated_file(inventory_reader, result)

        break


if __name__ == '__main__':
    main()
