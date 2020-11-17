import copy
import csv
from datetime import datetime
from datetime import timedelta
from datetimerange import DateTimeRange
import os.path


class Product:
    def __init__(self, line):
        for k, v in line.items():
            if k == '\ufeffSKU':
                self.sku = v
            elif k == 'DESCRIPTION':
                self.description = v
            elif k == 'DIMENSIONS (W X D X H)':
                self.dimensions = v
            elif k == 'WGT':
                self.weight = v
            elif k == 'PRICE CND':
                self.price = v
        self.parts = []
        self.col_ex = False
        self.qty = '0'
        if 'CD' in self.sku or 'CM' in self.sku:
            self.collection = self.sku.split('-', 1)[1].split('-', 1)[0]
        else:
            self.collection = self.sku.split('-', 1)[0]

    def add_part(self, ProductPart):
        self.parts.append(ProductPart)

    def parts_exist(self):
        if not self.parts:
            self.parts.append(self)

    def change_color_parts(self):
        color = self.sku.rsplit('-', 1)[1]
        for part in self.parts:
            if 'XX' in part.sku:
                part.sku = part.sku.rsplit('-', 1)[0] + '-' + color

    def update_qty(self):

        self.qty = self.parts[0].qty
        # -102  -  Pricelist Part SKU (i.e. PF-BAS-TWN-XX) not in vendor's report
        for part in self.parts:
            if part.qty == '-102':
                self.qty = part.qty
            elif int(part.qty) < int(self.qty):
                self.qty = part.qty

        if self.qty != '-102' and self.qty != '-50':
            if int(self.qty) < 0:
                self.qty = '0'

    def collection_exists(self):
        self.col_ex = True
        for part in self.parts:
            part.col_ex = True

    # def __repr__(self):
    #     return "{}".format(self.sku)
    def __repr__(self):
        return "{} : {}".format(self.sku, self.qty)


class ProductPart(Product):
    pass


class InventoryReportProduct:
    def __init__(self, line):
        if line['SKU'] != '' and 'other' not in line['SKU'].lower():
            time_range = self.get_timerange()
            if line['Next Deliv'] != '' and line['Next Deliv'] in time_range:
                line['Available'] = int(
                    line['Available']) + int(float(line['On PO'].replace(',', '')))
            self.qty = line['Available']
            self.sku = line['SKU'].strip()

    def get_timerange(self):

        datemask = '%Y-%m-%d'

        future_date = datetime.today() + timedelta(days=14)
        today_date = datetime.today()

        fday = datetime.strftime(future_date, datemask)
        tday = datetime.strftime(today_date, datemask)

        time_range = DateTimeRange(tday, fday)

        return time_range

    def __repr__(self):
        return "{} : {}".format(self.sku, self.qty)


class InventoryProduct:
    def __init__(self, line):
        self.sku = line['SKU']
        self.qty = line['Wholesale Furniture Brokers']
        self.parts = []
        self.add_sku_part()

    def add_sku_part(self):
        if '|' in self.sku:
            for s in self.sku.split('|'):
                part = InventoryProductPart(s)
                self.parts.append(part)
        else:
            part = InventoryProductPart(self.sku)
            self.parts.append(part)

    def update_stock(self):
        # -101  -  Inventory Part SKU in not on Price List Product SKU
        # -102  -  Pricelist Part SKU (i.e. PF-BAS-TWN-XX) not in vendor's report
        self.qty = self.parts[0].qty
        for part in self.parts:
            if part.qty == '-102':
                self.qty = part.qty
            elif part.qty == '-101':
                if self.qty != '-102':
                    self.qty = part.qty
            elif int(part.qty) < int(self.qty):
                self.qty = part.qty

        if self.qty != '-101' and self.qty != '-50' and self.qty != '-102':
            if int(self.qty) < 0:
                self.qty = '0'

    # def __repr__(self):
    #     return "{} : {}".format(self.sku, self.qty)
    def __repr__(self):
        return "{}".format(self.sku)


class InventoryProductPart(InventoryProduct):
    def __init__(self, sku):
        self.sku = sku
        self.qty = '0'

    def __repr__(self):
        return "{} : {}".format(self.sku, self.qty)


def collection_exists(products_pl, ven_products):
    result = []
    for product in products_pl:
        for ven_p in ven_products:
            if product.collection in ven_p.sku:
                product.collection_exists()
        result.append(product)
    return result


def assing_color(inv_skus, products_pl):

    not_updated_parts = []
    ppl_skus = []

    for i_product in inv_skus:
        for part in i_product.parts:
            for ppl in products_pl:
                if part.sku.rsplit('-', 1)[0] == ppl.sku.rsplit('-', 1)[0]:
                    temp = copy.deepcopy(ppl)
                    color = part.sku.rsplit('-', 1)[1]
                    temp.sku = ppl.sku.rsplit('-', 1)[0] + '-' + color
                    check_sku = temp.sku
                    temp.change_color_parts()
                    not_updated_parts.append(temp)
                    ppl_skus.append(check_sku)
                    break
            # Inventory Product
            if part.sku not in ppl_skus:
                part.qty = '-101'
                not_updated_parts.append(part)

    return not_updated_parts

# list


def products_to_parts(reader):
    # 1) if first item on the list, create a Product object
    # 2) else add the SKU to the Product as ProductPart

    count = 0
    products = []

    for line in reader:
        if line['\ufeffSKU'] != '':
            count += 1
            if count == 1:
                comp_product = Product(line)
            else:
                product_part = ProductPart(line)
                comp_product.add_part(product_part)
        else:
            if comp_product not in products:
                comp_product.parts_exist()
                products.append(comp_product)
            count = 0

    return products


def get_files_list():

    cwd = os.getcwd()

    inv_ven_dict = dict()
    ven_list = []
    inv_list = []

    for dirpath, dirnames, files in os.walk(cwd):
        for file_name in files:
            if file_name.endswith('.py') or 'updated' in file_name:
                pass
            elif 'export_1.csv' in file_name:
                inv_list.append(file_name)
            elif file_name.endswith('.csv'):
                ven_list.append(file_name)

    for i in inv_list:
        for v in ven_list:
            if 'n&d' in i and 'n&d' in v:
                inv_ven_dict['shopify_inventory/' + i] = 'vendor_report/' + v

    return inv_ven_dict


def update_sku_stock(inv_products, products_pl, ven_products):
    # in vendor's report
    color_exist = []
    part_exist = []

    result = dict()

    # check if vendor's report  contains collection from price list
    products_pl = collection_exists(products_pl, ven_products)

    # assign color to pricelist products' parts
    not_updated_parts = assing_color(inv_products, products_pl)

    # check if part exists in the vendor's report and assign stock value
    for p in not_updated_parts:
        if type(p) == Product:
            for part in p.parts:
                for ven_p in ven_products:
                    if part.sku == ven_p.sku:
                        part.qty = ven_p.qty
                        color_exist.append(part.sku)
                    if part.sku.rsplit('-', 1)[0] in ven_p.sku:
                        part_exist.append(part.sku)
                        continue
                if part.sku not in part_exist:
                    part.qty = '-102'
                if part.sku not in color_exist and part.qty != '-102':
                    part.qty = '-50'
            p.update_qty()

    # for p in not_updated_parts:
    #     if type(p) == Product:
    #         print(p, '|', p.parts)

    # update inventory products stock
    for inv_p in inv_products:
        for i_part in inv_p.parts:
            for part in not_updated_parts:
                if i_part.sku == part.sku:
                    i_part.qty = part.qty
            # print(i_part.sku, i_part.qty)
        inv_p.update_stock()
        # print(inv_p, inv_p.qty)
        result.update({inv_p: inv_p.qty})

    # print(result)

    return result


info_file = 'C:\\Users\\gosha\\Desktop\\WFB\\update-inventory\\__pycache__\\nad_sku_map.csv'
inv_ven_dict = get_files_list()

for inventory_file, vendor_file in inv_ven_dict.items():

    inv_products, ven_products, products_pl = [], [], []

    with open(info_file, 'r', encoding='utf8') as input_fule:
        reader = csv.DictReader(input_fule)

        products_pl = products_to_parts(reader)

    with open(vendor_file, 'r', encoding='utf8') as vendor_report:
        ven_reader = csv.DictReader(vendor_report)

        for line in ven_reader:
            invRepProduct = InventoryReportProduct(line)
            if hasattr(invRepProduct, 'sku'):
                ven_products.append(invRepProduct)

    with open(inventory_file, 'r', encoding='utf8') as inventory:
        inv_reader = csv.DictReader(inventory)

        for line in inv_reader:
            product = InventoryProduct(line)
            inv_products.append(product)

    result = update_sku_stock(inv_products, products_pl, ven_products)
