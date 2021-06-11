# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import argparse
import csv
from openpyxl import load_workbook
import os.path
import string
import sys

# Import invconv-specific modules
from modules import invconv_ini

ver_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")
with open(ver_path, "r") as version_file:
    ver_str = version_file.readline()

SUPPORTED_FORMAT_VER = 1

AXELOR_CSV_COLUMNS = [
    "procurementMethodSelect",
    "purchasesUnit_importId",
    "importId",
    "productSubTypeSelect",
    "purchaseCurrency_importId",
    "productTypeSelect",
    "salePrice",
    "picture_importId",
    "managPriceCoef",
    "purchasePrice",
    "defaultSupplierPartner_importId",
    "internalDescription",
    "salesUnit_importId",
    "name",
    "productFamily_importId",
    "code",
    "description",
    "productCategory_importId",
    "saleSupplySelect",
    "fullName",
    "saleCurrency_importId",
]
axelor_family_shorthand = {}
axelor_product_categories = {}
axelor_category_shorthand = {}
axelor_product_families = {}
axelor_product_types = []
axelor_units = {}
axelor_units_shorthand = {}
max_unit_shorthand = 0

parser = argparse.ArgumentParser(
    description="Converts inventory lists to a Axelor-compatible CSV format",
    epilog="Licensed under the 0BSD.",
    add_help=False,
)
parser.add_argument("-d", "--data-file", default="demo.ini", help="INI data file")
data_file = parser.parse_known_args()[0].data_file
data_parser = invconv_ini.data_parser
data_parser.read(data_file)
data_format_version = data_parser.getint("INFO", "INVCONV_FORMAT")
if data_format_version != SUPPORTED_FORMAT_VER:
    print(
        "FE: Data format version %s is unsupported.",
        data_format_version,
        file=sys.stderr,
    )
    sys.exit(1)
for key in data_parser["AXELOR_PRODUCT_CATEGORIES"]:
    axelor_product_categories[key] = int(data_parser["AXELOR_PRODUCT_CATEGORIES"][key])
    if key in data_parser["AXELOR_PRODUCT_CATEGORIES_ABREV"]:
        axelor_category_shorthand[key] = data_parser["AXELOR_PRODUCT_CATEGORIES_ABREV"][
            key
        ]
for key in data_parser["AXELOR_PRODUCT_FAMILIES"]:
    axelor_product_families[key] = int(data_parser["AXELOR_PRODUCT_FAMILIES"][key])
    if key in data_parser["AXELOR_PRODUCT_FAMILIES_ABREV"]:
        axelor_family_shorthand[key] = data_parser["AXELOR_PRODUCT_FAMILIES_ABREV"][key]
for key in data_parser["AXELOR_PRODUCT_TYPES"]:
    axelor_product_types += [key]
for key in data_parser["AXELOR_UNITS"]:
    axelor_units[key] = data_parser["AXELOR_UNITS"][key]
    if key in data_parser["AXELOR_UNITS_ABREV"]:
        axelor_units_shorthand[key] = data_parser["AXELOR_UNITS_ABREV"][key]
default_product_category = data_parser.get("CONSTANTS", "AXELOR_PRODUCT_CATEGORIES")
default_product_family = data_parser.get("CONSTANTS", "AXELOR_PRODUCT_FAMILIES")
default_product_type = data_parser.get("CONSTANTS", "AXELOR_PRODUCT_TYPES")
default_unit = data_parser.get("CONSTANTS", "AXELOR_UNITS")
max_unit_shorthand = data_parser.get("CONSTANTS", "MAX_UNIT_SHORTHAND")

parser.add_argument(
    "-h", "--help", action="help", help="show this help message and exit"
)
parser.add_argument(
    "-t",
    "--type",
    default="xslx",
    choices=["xslx"],
    help="The type of file that is being imported",
)
parser.add_argument("-v", "--version", action="version", version=ver_str)
parser.add_argument(
    "-c",
    "--category",
    choices=axelor_product_categories,
    default=default_product_category,
    help="Fallback product category to place in output",
)
parser.add_argument(
    "-f",
    "--family",
    choices=axelor_product_families,
    default=default_product_family,
    help="Fallback product family to place in output",
)
parser.add_argument(
    "-T",
    "--Type",
    choices=axelor_product_types,
    default=default_product_type,
    help="Fallback product type to place in output",
)
parser.add_argument(
    "-u",
    "--unit",
    choices=axelor_units,
    default=default_unit,
    help="Fallback unit to place in output",
)
parser.add_argument("input", help="Input file")

parser_args = parser.parse_args()
input_file = parser_args.input
fallback_category = parser_args.category
fallback_family = parser_args.family
fallback_type = parser_args.Type
fallback_unit = parser_args.unit

xslx_file = load_workbook(
    input_file, read_only=True, keep_vba=False, data_only=True, keep_links=False
)

csv_out = csv.writer(sys.stdout, dialect="excel")
csv_out.writerow(AXELOR_CSV_COLUMNS)

# This is used to populate the CSV file.
xslx_col_index = {
    "description": -1,
    "name": -1,
    "category": -1,
    "sales_UOM": -1,
    "purchase_UOM": -1,
}
xslx_headers = []

# A row with just a title would not fill up the entire
# max_column. As a result, there would be None at either
# the first or second position.
start_title_col = xslx_file.active.min_column
end_title_col = start_title_col + 1
# Assume the first line is not title unless otherwise found out.
xslx_header_row = xslx_file.active.min_row

for row in xslx_file.active.iter_rows(
    min_row=xslx_file.active.min_row,
    max_row=xslx_file.active.max_row,
    min_col=start_title_col,
    max_col=end_title_col,
    values_only=True,
):
    for cell in row:
        if cell is None:
            xslx_header_row = xslx_header_row + 1

if xslx_header_row >= xslx_file.active.max_row:
    print("FE: Can't find headers in " + input_file + ".")
    sys.exit(1)

for row in xslx_file.active.iter_rows(
    min_row=xslx_header_row,
    max_row=xslx_header_row,
    min_col=xslx_file.active.min_column,
    max_col=xslx_file.active.max_column,
    values_only=True,
):
    for cell in row:
        xslx_headers += [cell]
# col and row are indexed starting at 1.
header_index = 1
for header in xslx_headers:
    if (header.lower().find("descript") != -1) and (
        xslx_col_index["description"] == -1
    ):
        xslx_col_index["description"] = header_index
    # The name would be one of the first columns in a file.
    # In case a file has a header containing "name" and another
    # containing "ID", it should still have the correct one.
    elif (
        (header.lower().find("name") != -1) or (header.lower().find("id") != -1)
    ) and (xslx_col_index["name"] == -1):
        xslx_col_index["name"] = header_index
    elif (header.lower().find("cat") != -1) and (xslx_col_index["category"] == -1):
        xslx_col_index["category"] = header_index
    elif (
        (header.lower().find("unit") != -1) or (header.lower().find("uom") != -1)
    ) and (xslx_col_index["sales_UOM"] == -1):
        xslx_col_index["sales_UOM"] = header_index
    elif (
        (header.lower().find("unit") != -1)
        and ((header.lower().find("package") != -1) or header.lower().find("pkg") != -1)
        and (xslx_col_index["purchase_UOM"] == -1)
    ):
        xslx_col_index["purchase_UOM"] = header_index
    else:
        print(
            "Warning: column " + '"' + header + '"'
            " from " + input_file + " will be ignored.",
            file=sys.stderr,
        )
    header_index = header_index + 1
for required_header in xslx_col_index:
    if xslx_col_index[required_header] == -1:
        print("FE: " + required_header + " is not set", file=sys.stderr)
        sys.exit(1)

xslx_start_row = xslx_header_row + 1
xslx_min_col = -1
xslx_max_col = -1
for xslx_index in xslx_col_index.values():
    if xslx_index > xslx_max_col:
        xslx_max_col = xslx_index
    if (xslx_min_col == -1) or (xslx_index < xslx_min_col):
        xslx_min_col = xslx_index

cat_incr = {}
for row in xslx_file.active.iter_rows(
    min_row=xslx_start_row,
    max_row=xslx_file.active.max_row,
    min_col=xslx_min_col,
    max_col=xslx_max_col,
    values_only=True,
):
    row_dict = {}
    for csv_col in AXELOR_CSV_COLUMNS:
        row_dict[csv_col] = ""
    col_index = xslx_min_col
    for cell in row:
        if col_index == xslx_col_index["name"]:
            row_dict["name"] = cell
        elif col_index == xslx_col_index["description"]:
            row_dict["description"] = cell
            row_dict["internalDescription"] = cell
        elif col_index == xslx_col_index["category"]:
            valid_cat = False
            valid_fam = False
            for prod_cat in axelor_product_categories:
                if prod_cat == cell:
                    valid_cat = True
                    row_dict["productCategory_importId"] = axelor_product_categories[
                        cell
                    ]
                    break
            for prod_fam in axelor_product_families:
                if prod_fam == cell:
                    valid_fam = True
                    row_dict["productFamily_importId"] = axelor_product_families[cell]
                    break
            code_incr = ""
            ax_code_str = ""
            if valid_fam:
                ax_code_str = axelor_family_shorthand.get(
                    cell, cell.upper().replace(" ", "_")
                )
            elif valid_cat:
                ax_code_str = axelor_category_shorthand.get(
                    cell, cell.upper().replace(" ", "_")
                )
            else:
                ax_code_str = cell.upper().replace(" ", "_")
            code_incr = cat_incr.get(ax_code_str, "0000")
            cat_incr[ax_code_str] = code_incr
            row_dict["code"] = ax_code_str + "-" + code_incr
            if not valid_fam:
                row_dict["productFamily_importId"] = axelor_product_families[
                    fallback_family
                ]
            if not valid_cat:
                row_dict["productCategory_importId"] = axelor_product_categories[
                    fallback_category
                ]
            # Increment counter.
            code_incr_int = int(code_incr)
            code_incr_int = code_incr_int + 1
            if code_incr_int > 10:
                cat_incr[ax_code_str] = "".join("0" + "0" + "0" + str(code_incr_int))
            elif code_incr_int > 100:
                cat_incr[ax_code_str] = "".join("0" + "0" + str(code_incr_int))
            elif code_incr_int > 1000:
                cat_incr[ax_code_str] = "".join("0" + str(code_incr_int))
            else:
                cat_incr[ax_code_str] = str(code_incr_int)
        elif (col_index == xslx_col_index["sales_UOM"]) or (
            col_index == xslx_col_index["purchase_UOM"]
        ):
            unit_id = -1
            for unit in axelor_units:
                # These sections might contain int,
                # so str must be forced.
                if unit.lower() in str(cell).lower():
                    unit_id = axelor_units[unit]
            if unit_id == -1:
                digit_loc = -1
                string_index = 0
                while string_index < len(str(cell)):
                    char = str(cell)[string_index]
                    if char in string.digits:
                        digit_loc = string_index
                    string_index = string_index + 1
                if (digit_loc != -1) and (digit_loc != (len(str(cell)) - 1)):
                    # Test for a shortened unit form.
                    short_incr = 1
                    test_str = []
                    while (short_incr + string_index) < len(str(cell)):
                        test_str += str(cell)[string_index + short_incr]
                        short_incr = short_incr + 1
                    test_str = "".join(test_str)
                    for unit in axelor_units_shorthand:
                        if axelor_units_shorthand[unit] in test_str:
                            unit_id = axelor_units[unit]
            if unit_id == -1:
                unit_id = axelor_units[fallback_unit]
            if col_index == xslx_col_index["sales_UOM"]:
                row_dict["salesUnit_importId"] = unit_id
            elif col_index == xslx_col_index["purchase_UOM"]:
                row_dict["purchasesUnit_importId"] = unit_id
            else:
                pass
        else:
            pass
        col_index = col_index + 1
    # Add values not directly based on XSLX file.
    row_dict["productTypeSelect"] = fallback_type
    row_dict["fullName"] = "[" + row_dict["code"] + "]" + " " + row_dict["name"]

    csv_out.writerow(row_dict.values())
    row_dict.clear()

xslx_file.close()
