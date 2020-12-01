import csv
import os
import sys

file_name_dict = {'bestar_ca_report.csv': 'bestarinventorylistnextdate', 'we_ca_report.csv': 'WE Inv Report - ', 'modloft_us_report.csv': 'modloft_inventory',
                  'modloft_ca_report.csv': 'Modloft_Product_data_', 'zuomod_ca_report.csv': 'zuomod.ca_export_', 'brassex_ca_report.csv': 'Stock-Update-125',
                  'mobital_us_report.csv': 'Mobital Vancouver Inventory_Weekly', 'mobital_ca_report.csv': 'Mobital Vancouver Inventory_11960_CSV',
                  'corcoran_ca_report.csv': 'Specs sheet-inventory Corcoran ', 'n&d_po_report.csv': 'WFB - Open PO detail N&D', 'n&d_ca_report.csv': 'WFB_Inventory_file_'}


def change_filename():

    cwd = os.getcwd()

    for dirpath, dirnames, files in os.walk(cwd):
        for file_name in files:
            for k, v in file_name_dict.items():
                if v in file_name:
                    os.rename('vendor_report/' + file_name,
                              'vendor_report/' + k)
