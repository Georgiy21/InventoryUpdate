import os.path
import fnmatch
from datetimerange import DateTimeRange
from datetime import timedelta
from datetime import datetime
import csv

vendors = {'Bestar': 'bestar_ca_export_1', 'Walker Edison': 'we_ca_export_1', 'Modloft Canada': 'modloft_ca_export_1', 'Modloft USA': 'modloft_us_export_1',
           'Zuo Modern': 'zuomod_ca_export_1', 'Brassex': 'brassex_ca_export_1', 'Mobital': 'mobital_ca_export_1',
           'Corcoran': 'corcoran_ca_export_1', 'Night and Day': 'n&d_ca_export_1'}


class InventoryProduct:

    def __init__(self, sku):
        self.sku = sku
        self.qty = ''
        self.vendor = ''
        self.parts = []

    def add_sku_part(self):
        if '|' in self.sku:
            for s in self.sku.split('|'):
                part = InventoryProductPart(s)
                self.parts.append(part)
        else:
            part = InventoryProductPart(self.sku)
            self.parts.append(part)

    def update_stock(self):
        self.qty = self.parts[0].qty
        for part in self.parts:
            if part.qty == '-50':
                self.qty = '-50'
            elif int(part.qty) < int(self.qty):
                self.qty = part.qty

    def __repr__(self):
        return "{}".format(self.sku)


class InventoryProductPart(InventoryProduct):
    pass


class Product:

    def __init__(self, line, vendor):
        self.vendor = vendor
        self.get_product_info(line)

    def get_timerange(self):

        if self.vendor.lower() == 'brassex':
            datemask = '%Y-%m-%d'
        else:
            datemask = '%m-%d-%Y'

        future_date = datetime.today() + timedelta(days=7)
        today_date = datetime.today()

        fday = datetime.strftime(future_date, datemask)
        tday = datetime.strftime(today_date, datemask)

        time_range = DateTimeRange(tday, fday)

        return time_range

    def get_product_info(self, line):
        ven_low = self.vendor.lower()
        for k, v in line.items():
            if 'mobital' in ven_low:
                self.sku = line['ItemNumber'].replace('-', '').strip()
                if line['Discontinued'] == str(1):
                    self.qty = '-50'
                else:
                    self.qty = line['Quantity on Hand']
                break
            if 'bestar' in ven_low:
                if k == 'ITEM' or k == 'ï»¿ITEM' or k == '\ufeffITEM':
                    self.sku = v
                if line['NEXT DATE'] != '':
                    time_range = self.get_timerange()
                    if line['NEXT DATE'] in time_range:
                        line['QTY'] = float(line['QTY']) + \
                            float(line['NEXT QTY'].replace(',', ''))
                try:
                    self.qty = int(float(line['QTY']))
                except ValueError:
                    self.qty = 0
                break
            if 'we' in ven_low:
                self.sku = line['SKU']
                self.qty = line['Stock']
                break
            if 'brassex' in ven_low:
                self.sku = line['Model#']
                if line['ETA'] != '':
                    time_range = self.get_timerange()
                    if line['ETA'] in time_range:
                        line['Quantity'] = int(
                            line['Quantity']) + int(line['In-transit QTY'])
                self.qty = line['Quantity']
                break
            if 'zuomod' in ven_low:
                self.sku = line['ITEN NO']
                self.qty = line['QTY']
                break
            # not tested
            if 'mlily' in ven_low:
                if line['SKU'] != '':
                    self.sku = line['SKU']
                if line['Inventory'] != '':
                    self.qty = line['Inventory']
                break
            # if 'modloft' in ven_low:
            #     self.sku = line['Item Number']
            #     self.qty = line['Qty on hand']
            #     break

    def __repr__(self):
        return "{} : {}".format(self.sku, self.qty)

    def __str__(self):
        return "{} - {}".format(self.sku, self.qty)


def get_files_dict():

    cwd = os.getcwd()

    inv_ven_dict = dict()
    ven_list, inv_list = [], []

    for dirpath, dirnames, files in os.walk(cwd):
        for file_name in files:
            if not file_name.endswith('.py') and 'updated' not in file_name.lower():
                if 'export_1.csv' in file_name:
                    inv_list.append(file_name)
                elif 'report.csv' in file_name:
                    ven_list.append(file_name)

    for i in inv_list:
        file_name = i.rsplit('_', 2)[0].strip()
        for v in ven_list:
            if file_name in v:
                inv_ven_dict['shopify_inventory/' +
                             i] = 'vendor_report/' + v
    # print(inv_ven_dict)
    return inv_ven_dict


def remove_first_line(inp_file):
    old_file = []
    with open(inp_file, 'r') as input_file:
        reader = csv.reader(input_file)

        for line in reader:
            old_file.append(line)

    if old_file[0][1] != '':
        pass
    else:
        old_file.pop(0)

        with open(inp_file, 'w', newline='') as output_file:
            writer = csv.writer(output_file)

            for row in old_file:
                writer.writerow(row)

        print('first line removed')
        output_file.close()

    input_file.close()


def split_sku(inv_list):
    result = []
    inv_skus = []
    for p in inv_list:
        p.add_sku_part()
        for part in p.parts:
            result.append(part)
        inv_skus.append(p)
    return result, inv_skus


def combine_sku(result, inv_list):
    res_dict = dict()

    for i_product in inv_list:
        for part in i_product.parts:
            for result_sku, result_qty in result.items():
                if part.sku == result_sku.sku:
                    part.qty = result_qty
                    break
        i_product.update_stock()
        res_dict.update({i_product: i_product.qty})

    return res_dict


def update_inventory(inv_list, ven_list, vendor_name):
    result = dict()
    present_sku = []

    if 'brassex' in vendor_name.lower() or 'modloft' in vendor_name.lower():
        inv_list, inv_skus = split_sku(inv_list)

    for i_p in inv_list:
        for v_p in ven_list:
            if i_p.sku == v_p.sku:
                result.update({i_p: v_p.qty})
                present_sku.append(i_p.sku)
        # discontinued
        if i_p.sku not in present_sku:
            result.update({i_p: '-50'})

    if 'brassex' in vendor_name.lower() or 'modloft' in vendor_name.lower():
        result = combine_sku(result, inv_skus)

    return result


def gen_updated_file(inventory_fields, values, vendor_name, inventory):

    filename = 'updated_{}.csv'.format(
        vendor_name.lower().replace(' ', '_'))

    with open(filename, 'w', newline='', encoding='utf8') as updated_file:
        writer = csv.DictWriter(updated_file, fieldnames=inventory_fields)
        writer.writeheader()

        with open(inventory, 'r', encoding='utf8') as inventory_file:
            inventory_reader = csv.DictReader(inventory_file)

            for line in inventory_reader:
                for k, v in values.items():
                    if k.sku == line['SKU']:
                        line.update({'Wholesale Furniture Brokers': v})
                writer.writerow(line)

    updated_file.close()

    for k, v in vendors.items():
        if v in inventory.lower():
            print('UPDATED ', k, ' FILE IS PRINTED')


def safety_policy(result):
    for k, v in result.items():
        if v == '-50':
            continue
        elif int(float(v)) < 10:
            result[k] = "0"


def get_inventory_columns(inventory):

    columns = []

    with open(inventory, 'r', encoding='utf8') as inventory_file:
        inventory_reader = csv.DictReader(inventory_file)

        for line in inventory_reader:
            for k in line.keys():
                columns.append(k)
            break

    return columns


def main():

    import rename_files
    rename_files.change_filename()

    vendor_name = ''
    inv_ven_dict = get_files_dict()

    for inventory, vendor in inv_ven_dict.items():
        result = dict()

        # get Vendor's name
        for k, v in vendors.items():
            if v in inventory:
                vendor_name = k

        inventory_fields = get_inventory_columns(inventory)

        if vendor_name == 'Night and Day':
            import night_and_day_module
            result = night_and_day_module.result
        elif 'Modloft' in vendor_name:
            import modloft_module
            results = modloft_module.results
            for i in results:
                for file_name, m_result in i.items():
                    if file_name in inventory:
                        result = m_result
        elif vendor_name == 'Corcoran':
            import corcoran_module
            result = corcoran_module.result
        else:
            inv_products = []
            ven_products = []

            with open(inventory, 'r', encoding='utf8') as inventory_file:
                inventory_reader = csv.DictReader(inventory_file)

                for line in inventory_reader:
                    product = InventoryProduct(
                        line['SKU'])
                    inv_products.append(product)
                    product.vendor = vendor_name

                inventory_file.seek(0)

                # file preprocesing
                if 'brassex' in vendor.lower():
                    remove_first_line(vendor)

                with open(vendor, 'r') as vendor_file:

                    vendor_reader = csv.DictReader(vendor_file)

                    for line in vendor_reader:
                        product = Product(line, vendor)
                        if hasattr(product, 'sku'):
                            ven_products.append(product)

                vendor_file.close()

            inventory_file.close()

            result = update_inventory(
                inv_products, ven_products, vendor_name)

        # safety policy
        safety_policy_vendors = ['Bestar', 'Walker Edison']
        for v in safety_policy_vendors:
            if vendor_name == v:
                safety_policy(result)

        gen_updated_file(inventory_fields, result, vendor_name, inventory)


if __name__ == '__main__':
    main()
