# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import argparse
import csv
from openpyxl import load_workbook
import sys

with open("VERSION", "r") as version_file:
    ver_str = version_file.readline()

parser = argparse.ArgumentParser(
    description="Converts inventory lists to a Axelor-compatible CSV format",
    epilog="Licensed under the 0BSD.")
parser.add_argument("-t", "--type", default="xslx",
    choices=["xslx"],
    help="The type of file that is being imported")
parser.add_argument("-v", "--version", action="version", version=ver_str)
parser.add_argument("input", help="Input file")
parser_args = parser.parse_args()
input_file = parser_args.input

xslx_file = load_workbook(
    input_file,
    read_only=True,
    keep_vba=False,
    data_only=True,
    keep_links=False)

for sheet in xslx_file:
    for row in sheet.iter_rows(
        min_row=sheet.min_row,
        max_row=sheet.max_row,
        min_col=sheet.min_column,
        max_col=sheet.max_column,
        values_only=True):
        csv_out = csv.writer(sys.stdout, dialect="excel")
        csv_out.writerow(row)
xslx_file.close()