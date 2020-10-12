import pandas as pd
import csv
import collections
import fnmatch
import os.path
from os import path
from datetime import datetime
from datetimerange import DateTimeRange
from datetime import timedelta

#! ALL FILES MUST BE IN .CSV FORMAT !#

# ? Architucture: have one inventory export file of one vendor and one vendor file
# ? EX: inventory_export_1.csv & Mobital Vancouver Inventory_Weekly.csv


vendors = ['Walker Edison', 'Brassex', 'Primo', 'Hush', 'Mobital',
           'Night and Day', 'Vifah', 'MLily', 'Zuo', 'Bestar', 'CDI']


exported_files = []

cwd = os.path.dirname(__file__)

inventory_fields = ["Handle", "Title", "Option1 Name", "Option1 Value",	"Option2 Name",	"Option2 Value",
                    "Option3 Name", "Option3 Value", "SKU", "HS Code", "COO", "Wholesale Furniture Brokers"]

# Make product quantity 0 if the quantity is <= 10


def safety_policy(result):
    for k, v in result.items():
        if v == '-50':
            continue
        elif int(float(v)) < 10:
            result[k] = "0"

# generate a company file with updated product quantity ready to be imported to Shopify Inventory


def gen_updated_file(inventory_reader, values):
    with open('updated_inventory.csv', 'w+', newline='', encoding='utf8') as updated_file:
        writer = csv.DictWriter(updated_file, fieldnames=inventory_fields)
        for row in inventory_reader:
            for k, v in values.items():
                if row['SKU'] == k and row['Wholesale Furniture Brokers'] != v:
                    # print("Row Before: ", row)
                    row.update({'Wholesale Furniture Brokers': v})
                    # print("Row After: " , row)
            writer.writerow(row)

    updated_file.close()
    print('UPDATED FILE IS PRINTED')


def primo_convert_pdf(file):

    with open(file) as test_file:
        reader = csv.reader(test_file)
        updated_file = []
        for line in reader:
            if line[1] == 'Hand' or line[1] == '' or line[1] == 'Product (SKU)':
                continue
            else:
                updated_file.append((line[1], line[3]))

    return updated_file

# remove first line of the Brassex file and rewrite the rest of the lines to a new file


def update_file_format(inp_file):
    with open('Brassex.csv', 'w+', newline='') as new_file:
        writer = csv.writer(new_file)
        for row in csv.reader(inp_file):
            if row[1] != '':
                writer.writerow(row)
    new_file.close()

# generate a dictionary {'SKU' : 'Quantity'} for both company and vendor and update the quantity


def update_qty(inv_dict, ven_dict):

    # Products from inventory that are not in vendor
    discontinued_items = [
        k for k in inv_dict.keys() if k not in ven_dict.keys()]

    # print(discontinued_items)

    # Products whose date < today's date, hence qty = ''
    # empty_qty = {k: ven_dict[k] for k in ven_dict if ven_dict[k] == ''}
    # # Products whose qty isn't empty
    # pres_qty = {k: ven_dict[k] for k in ven_dict if ven_dict[k] != ''}

    # Products from inventory whose price isn't updated
    diff_items = {
        k: inv_dict[k] for k in inv_dict if k in ven_dict and inv_dict[k] != ven_dict[k]}

    # print("\ndiff_items: " , diff_items)

    # Update the inventory price with vendor's
    diff_items.update((k, ven_dict[k])
                      for k in ven_dict.keys() & diff_items.keys())
    # print("\n[UPDATED] Different items: " , diff_items)

    # Updated SKUs and QTY
    inv_dict.update((k, diff_items[k])
                    for k in diff_items.keys() & inv_dict.keys())

    # Update discontinued products with QTY=-50
    inv_dict.update((k, "-50") for k in discontinued_items)

    # print("\nUpdated inventory: " , inv_dict)
    return inv_dict


def update_set_skus(inv_dict):
    set_sku = []
    inv_list = []

    for k, v in inv_dict.items():
        if '|' in k:
            group = []
            for i in k.split('|'):
                group.append(i)
                inv_list.append((i, v))
            set_sku.append(group)
        else:
            inv_list.append((k, v))

    inv_dict = dict(inv_list)

    return inv_dict, set_sku


def combine_skus(temp, inv_dict):

    res = []

    for s, q in temp.items():
        for k, v in inv_dict.items():
            quantity = '0'
            if s in k.split('|'):
                if int(str(q)) <= int(quantity):
                    inv_dict[k] = q

    result = dict(res)

    return result


def main():
    # tup1 for inventory, tup2 for vendor
    tup1, tup2 = [], []

    # Get 1 WEEK daterange from today's date
    datemask = '%m-%d-%Y'

    future = datetime.today() + timedelta(days=7)
    fday = datetime.strftime(future, datemask)

    tday = datetime.today().strftime(datemask)
    today = datetime.strptime(tday, datemask)

    time_range = DateTimeRange(tday, fday)
    # print(time_range)

    # Generate a list of vendors' csv files
    for dirpath, dirnames, files in os.walk(cwd):
        for file_name in files:
            if file_name == 'inventory_export_1.csv' or file_name.endswith('.py'):
                pass
            else:
                exported_files.append(file_name)

    # print(exported_files)

    try:
        with open("inventory_export_1.csv", "r+", encoding='utf8') as inventory_file:
            inventory_reader = csv.DictReader(inventory_file)

            for line in inventory_reader:
                tup1.append((line['SKU'], line['Wholesale Furniture Brokers']))
            inv_dict = dict(tup1)

            for i in exported_files:
                with open(i, 'r') as vendor_file:
                    if fnmatch.fnmatch(i, 'Brassex Inventory-*'):

                        print("Brassex report detected")

                        s_inv_dict, set_sku = update_set_skus(inv_dict)

                        datemask = '%Y-%m-%d'

                        future = datetime.today() + timedelta(days=7)
                        fday = datetime.strftime(future, datemask)

                        tday = datetime.today().strftime(datemask)
                        today = datetime.strptime(tday, datemask)

                        time_range = DateTimeRange(tday, fday)

                        update_file_format(vendor_file)

                        with open('Brassex.csv', 'r+') as vendor:
                            vendor_reader = csv.DictReader(vendor)

                            for line in vendor_reader:
                                if line['ETA DATE'] != '':
                                    if line['ETA DATE'] in time_range:
                                        line['AVAILABLE QTY'] = line['IN-TRANSIT QTY']
                                tup2.append(
                                    (line['MODEL#'], line['AVAILABLE QTY']))
                            ven_dict = dict(tup2)

                            temp = update_qty(s_inv_dict, ven_dict)

                            result = combine_skus(temp, inv_dict)

                            inventory_file.seek(0)
                            # gen_updated_file(inventory_reader, result)

                    elif fnmatch.fnmatch(i, 'WE*'):

                        print("Walker Edison report detected")

                        vendor_reader = csv.DictReader(vendor_file)

                        for line in vendor_reader:
                            tup2.append((line['SKU'], line['Stock']))
                        ven_dict = dict(tup2)

                        result = update_qty(inv_dict, ven_dict)
                        inventory_file.seek(0)

                        safety_policy(result)

                        gen_updated_file(inventory_reader, result)

                    elif fnmatch.fnmatch(i, 'Zuo Modern*'):

                        vendor_reader = csv.DictReader(vendor_file)

                        for line in vendor_reader:
                            tup2.append((line['ITEN NO'], line['QTY']))
                        ven_dict = dict(tup2)

                        result = update_qty(inv_dict, ven_dict)
                        inventory_file.seek(0)
                        gen_updated_file(inventory_reader, result)

                    elif fnmatch.fnmatch(i, 'Mobital*'):
                        print('Mobital Detected')
                        vendor_reader = csv.DictReader(vendor_file)

                        # datemask = '%d/%m/%Y'

                        # future = datetime.today() + timedelta(days=7)
                        # fday = datetime.strftime(future, datemask)

                        # tday = datetime.today().strftime(datemask)
                        # today = datetime.strptime(tday, datemask)

                        # time_range = DateTimeRange(tday, fday)
                        # # print(time_range)

                        for line in vendor_reader:
                            if line['Discontinued'] == str(1):
                                tup2.append((line['ItemNumber'], '-50'))
                            else:
                                tup2.append(
                                    (line['ItemNumber'].replace('-', '').strip(), line['Quantity on Hand']))

                        # for line in vendor_reader:
                        #     if line['Discontinued'] == str(1):
                        #         tup2.append((line['ItemNumber'], '-50'))
                        #     else:
                        #         result = ''
                        #         if line['Item Next Availability Date'] != '':
                        #             if line['Item Next Availability Date'] in time_range:
                        #                 result = int(line['Quantity on Hand']) + int(line['Quantity On Order']) - \
                        #                     int(line['Quantity Backordered'])
                        #             else:
                        #                 result = int(
                        #                     line['Quantity on Hand']) - int(line['Quantity Backordered'])
                        #         else:
                        #             result = int(
                        #                 line['Quantity on Hand']) - int(line['Quantity Backordered'])

                        #         line['Quantity on Hand'] = result if result > 0 else '0'
                        #         tup2.append(
                        #             (line['ItemNumber'], line['Quantity on Hand']))

                        ven_dict = dict(tup2)

                        result = update_qty(inv_dict, ven_dict)
                        inventory_file.seek(0)
                        gen_updated_file(inventory_reader, result)

                    elif fnmatch.fnmatch(i, 'Primo*'):

                        ven_dict = dict(primo_convert_pdf(i))

                        result = update_qty(inv_dict, ven_dict)
                        inventory_file.seek(0)
                        gen_updated_file(inventory_reader, result)

                    elif fnmatch.fnmatch(i, 'bestar inventory*'):

                        print("Bestar report detected")

                        vendor_reader = csv.DictReader(vendor_file)

                        for line in vendor_reader:
                            if line['NEXT DATE'] != '':
                                if line['NEXT DATE'] in time_range:
                                    line['QTY'] = line['NEXT QTY']
                            try:
                                tup2.append((line['ITEM'], line['QTY']))
                            except KeyError:
                                tup2.append((line['ï»¿ITEM'], line['QTY']))
                        ven_dict = dict(tup2)

                        result = update_qty(inv_dict, ven_dict)
                        # print(result)

                        inventory_file.seek(0)

                        safety_policy(result)

                        gen_updated_file(inventory_reader, result)

                    elif fnmatch.fnmatch(i, 'Night_&_Day*'):
                        pass

                    elif fnmatch.fnmatch(i, 'MLily*'):

                        vendor_reader = csv.DictReader(vendor_file)

                        for line in vendor_reader:
                            if line['SKU'] == '':
                                continue
                            else:
                                tup2.append((line['SKU'], line['Inventory']))

                        ven_dict = dict(tup2)

                        result = update_qty(inv_dict, ven_dict)
                        inventory_file.seek(0)

                        gen_updated_file(inventory_reader, result)

                vendor_file.close()
        inventory_file.close()

    except(FileExistsError, FileNotFoundError):
        pass


if __name__ == '__main__':
    main()
