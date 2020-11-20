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
        self.qty = '0'
        self.part_exist = True
        self.color_exist = True

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
        # -102  -  Pricelist Part SKU (i.e. PF-BAS-TWN-XX) not in vendor's report
        # -50   -  Color not in vendor's report
        qty = self.parts[0].qty

        if not self.part_exist:
            self.qty = '-102'
        elif self.part_exist and not self.color_exist:
            self.qty = '-50'
        else:
            for part in self.parts:
                if int(part.qty) < int(qty):
                    qty = part.qty

            if int(qty) < 0:
                self.qty = '0'
            else:
                self.qty = qty

    def exist(self):
        for part in self.parts:
            if part.part_exist == False:
                self.part_exist = False
                self.qty = part.qty = '-102'

    def is_color_exist(self):
        for part in self.parts:
            if part.color_exist == False:
                self.color_exist = False
                if part.part_exist:
                    part.qty = '-50'

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
        self.product_exist = True
        self.color_exist = True

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
        # -50   -  Color not in vendor's report
        qty = self.parts[0].qty

        for part in self.parts:
            if part.qty == '-102':
                self.qty = part.qty
            elif not self.product_exist and part.qty != '-102':
                pass
            elif not part.color_exist and part.qty != '-102':
                self.qty = '-50'
            else:
                if int(part.qty) < int(qty):
                    qty = part.qty

                self.qty = qty

    def is_product_exist(self):
        # -101  -  Inventory Part SKU in not on Price List Product SKU
        for part in self.parts:
            if part.product_exist == False:
                self.product_exist = False
                self.qty = part.qty = '-101'

    def __repr__(self):
        return "{} : {}".format(self.sku, self.qty)

    # def __repr__(self):
    #     return "{}".format(self.sku)


class InventoryProductPart(InventoryProduct):
    def __init__(self, sku):
        self.sku = sku
        self.qty = '0'
        self.product_exist = True
        self.color_exist = True

    def __repr__(self):
        return "{} : {}".format(self.sku, self.qty)


# check if vendor's report contains PART SKU from pricelist
def check_part_exist(products_pl, ven_products):
    part_exist = []

    for product in products_pl:
        for part in product.parts:
            for ven_p in ven_products:
                if 'XX' in part.sku:
                    if part.sku.rsplit('-', 1)[0] in ven_p.sku:
                        part_exist.append(part.sku)
                else:
                    if part.sku == ven_p.sku:
                        part_exist.append(part.sku)
            if part.sku not in part_exist:
                part.part_exist = False
        product.exist()


# assign color to pricelist products' parts
def assing_color(inv_skus, products_pl):
    not_updated_product, ppl_skus = [], []

    for product in inv_skus:
        for part in product.parts:
            for ppl in products_pl:
                if part.sku.rsplit('-', 1)[0].strip() == ppl.sku.rsplit('-', 1)[0].strip():
                    temp = copy.deepcopy(ppl)
                    color = part.sku.rsplit('-', 1)[1]
                    temp.sku = ppl.sku.replace('XX', color)
                    temp.change_color_parts()
                    not_updated_product.append(temp)
                    ppl_skus.append(temp.sku)
                    break
            # Inventory Product
            if part.sku not in ppl_skus:
                part.product_exist = False
        product.is_product_exist()
        product.update_stock()

    return not_updated_product


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


def add_column_name(vendor_file):
    ven_products, new_file = [], []
    is_col_name_set = False

    with open(vendor_file, 'r', encoding='utf8') as read_file:
        reader = csv.reader(read_file)
        for line in reader:
            new_file.append(line)
    read_file.close()

    for line in new_file:
        if line[3] != 'SKU':
            line[3] = 'SKU'
            is_col_name_set = True
        break

    if is_col_name_set == True:
        with open(vendor_file, 'w', newline='') as output_file:
            writer = csv.writer(output_file)

            for line in new_file:
                writer.writerow(line)
        output_file.close()

    with open(vendor_file, 'r', encoding='utf8') as vendor_read_file:
        ven_reader = csv.DictReader(vendor_read_file)
        for line in ven_reader:
            invRepProduct = InventoryReportProduct(line)
            if hasattr(invRepProduct, 'sku'):
                ven_products.append(invRepProduct)
    vendor_read_file.close()

    return ven_products


def assign_qty(inv_products, ven_products, not_updated_product):
    color_exist = []
    result = dict()

    # update products' qty if color exist
    for p in not_updated_product:
        for part in p.parts:
            for ven_p in ven_products:
                if part.sku == ven_p.sku:
                    part.qty = ven_p.qty
                    color_exist.append(part.sku)
                    break
            if part.sku not in color_exist:
                part.color_exist = False
        p.is_color_exist()
        p.update_qty()

    # for p in not_updated_product:
    #     print(p, p.parts)

    for inv_p in inv_products:
        for i_part in inv_p.parts:
            for part in not_updated_product:
                if i_part.sku == part.sku:
                    i_part.qty = part.qty
                    if part.color_exist == False:
                        i_part.color_exist = False
        inv_p.update_stock()
        # print(inv_p, inv_p.parts)
        result.update({inv_p: inv_p.qty})

    return result


def update_sku_stock(inv_products, products_pl, ven_products):

    # check if vendor's report contains PART from price list
    check_part_exist(products_pl, ven_products)

    # assign color to pricelist products' parts
    not_updated_product = assing_color(inv_products, products_pl)

    # update inventory products stock
    result = assign_qty(inv_products, ven_products, not_updated_product)

    return result


info_file = 'C:\\Users\\gosha\\Desktop\\WFB\\update-inventory\\__pycache__\\nad_sku_map.csv'
inv_ven_dict = get_files_list()

for inventory_file, vendor_file in inv_ven_dict.items():

    inv_products, ven_products, products_pl = [], [], []

    with open(info_file, 'r', encoding='utf8') as input_fule:
        reader = csv.DictReader(input_fule)

        products_pl = products_to_parts(reader)

    ven_products = add_column_name(vendor_file)

    with open(inventory_file, 'r', encoding='utf8') as inventory:
        inv_reader = csv.DictReader(inventory)

        for line in inv_reader:
            product = InventoryProduct(line)
            inv_products.append(product)

    result = update_sku_stock(inv_products, products_pl, ven_products)
