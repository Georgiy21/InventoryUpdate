import csv
import os


class CanadianProduct:
    def __init__(self, line):
        self.sku = line['\ufeffSKU']
        self.qty = line['STOCK CA']
        self.country = 'Canada'

    # def __repr__(self):
    #     return "{}".format(self.sku)

    def __repr__(self):
        return "{} : {}".format(self.sku, self.qty)


class UsProduct(CanadianProduct):
    def __init__(self, line):
        self.sku = line['Item Number']
        self.qty = line['Qty on hand']
        self.country = 'US'


class InventoryProduct:
    def __init__(self, sku, qty):
        self.sku = sku
        self.qty = qty
        self.parts = []
        self.is_updated = False
        self.country = ''

    def add_sku_part(self):
        if '|' in self.sku:
            for s in self.sku.split('|'):
                part = InventoryProduct(s, 0)
                self.parts.append(part)
        else:
            part = InventoryProduct(self.sku, self.qty)
            self.parts.append(part)

    def update_stock(self):
        qty = self.parts[0].qty

        for part in self.parts:
            if part.is_updated == False:
                self.qty = part.qty = -50
                part.is_updated = True
                self.country = part.country = 'Discontinued'
            else:
                if part.qty < qty:
                    qty = part.qty

                self.qty = qty
                self.country = part.country

        self.is_updated = True

    # def __repr__(self):
    #     return "{} : {}".format(self.sku, self.qty)

    def __repr__(self):
        return "{}".format(self.sku)


def get_files_list():
    result = []
    cwd = os.getcwd()

    ven_list, inv_list = [], []

    for dirpath, dirnames, files in os.walk(cwd):
        for file_name in files:
            if 'updated' not in file_name.lower():
                if 'modloft_ca_export_1.csv' == file_name or 'modloft_us_export_1.csv' == file_name:
                    inv_list.append('shopify_inventory/' + file_name)
                elif 'modloft' in file_name and 'inventory' in file_name.lower():
                    ven_list.append('vendor_report/' + file_name)

    for i in inv_list:
        inv_ven_dict = dict()
        if '_ca_' in i:
            inv_ven_dict[i] = ven_list
        else:
            for v in ven_list:
                if '_us_' in v:
                    inv_ven_dict[i] = [v]
        result.append(inv_ven_dict)

    return result


def split_sku(inv_list):
    result = []

    for p in inv_list:
        p.add_sku_part()
        for part in p.parts:
            result.append(part)

    return result


def get_result(inv_products, inventory_file):
    result, inventory = dict(), dict()

    for p in inv_products:
        p.update_stock()
        inventory.update({p: p.qty})

    result.update({inventory_file: inventory})

    return result


def update_inventory(inv_list, ven_list):
    for i_p in inv_list:
        for v_p in ven_list:
            if i_p.sku == v_p.sku and i_p.is_updated == False:
                i_p.qty = v_p.qty
                i_p.is_updated = True


results = []

file_list = get_files_list()

for inv_file_dict in file_list:
    for inventory_file, ven_file_list in inv_file_dict.items():

        inv_products = []

        with open(inventory_file, 'r', encoding='utf8') as inventory:
            inv_reader = csv.DictReader(inventory)

            for line in inv_reader:
                product = InventoryProduct(line['SKU'], int(
                    line['Wholesale Furniture Brokers']))
                inv_products.append(product)

        inv_products_parts = split_sku(inv_products)

        for ven_file in ven_file_list:
            ven_products = []
            with open(ven_file, 'r', encoding='utf8') as vendor_read_file:
                ven_reader = csv.DictReader(vendor_read_file)

                for line in ven_reader:
                    if '_ca_' in ven_file:
                        product = CanadianProduct(line)
                    else:
                        product = UsProduct(line)
                    ven_products.append(product)

            update_inventory(inv_products_parts, ven_products)
        results.append(get_result(inv_products, inventory_file))
