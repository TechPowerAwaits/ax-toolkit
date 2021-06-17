# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import argparse
from openpyxl import load_workbook
import os.path
import string
import sys

# Import invconv-specific modules
from modules import axm_parser
from modules import common
from modules import invconv_logic
from modules import panic_handler

ver_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")
with open(ver_path, "r") as version_file:
    ver_str = version_file.readline()

parser = argparse.ArgumentParser(
    description="Converts inventory lists to a Axelor-compatible CSV format",
    epilog="Licensed under the 0BSD.",
    add_help=False,
)
parser.add_argument("-d", "--data-file", default="demo.ini", help="INI data file")
data_file = parser.parse_known_args()[0].data_file
with open(data_file) as data_fptr:
    common.init(data_fptr)

parser.add_argument("-m", "--map-file", default="default.axm", help="AXM map file")
parser.add_argument(
    "-h", "--help", action="help", help="show this help message and exit"
)
parser.add_argument("-v", "--version", action="version", version=ver_str)

parser.add_argument(
    "-t",
    "--type",
    default="xlsx",
    choices=["xlsx"],
    help="The type of file that is being imported",
)
parser.add_argument(
    "-c",
    "--category",
    choices=common.axelor_product_categories,
    default=common.fallback_category,
    help="Fallback product category to place in output",
)
parser.add_argument(
    "-f",
    "--family",
    choices=common.axelor_product_families,
    default=common.fallback_family,
    help="Fallback product family to place in output",
)
parser.add_argument(
    "-T",
    "--Type",
    choices=common.axelor_product_types,
    default=common.fallback_type,
    help="Fallback product type to place in output",
)
parser.add_argument(
    "-u",
    "--unit",
    choices=common.axelor_units,
    default=common.fallback_unit,
    help="Fallback unit to place in output",
)
parser.add_argument("input", nargs="+", help="Input file(s)")
parser_args = parser.parse_args()
input_files = parser_args.input
map_file = parser_args.map_file
common.fallback_category = parser_args.category
common.fallback_family = parser_args.family
common.fallback_type = parser_args.Type
common.fallback_unit = parser_args.unit

# On some xlsx files, the max_row and max_col
# cannot be read.
max_rows = {}
max_cols = {}

# Store dictionary of header names for future
# reference.
file_ws_dict = {}

for input_file in input_files:
    file_ws_dict[input_file] = []
    xlsx_file = load_workbook(
        input_file, read_only=True, keep_vba=False, data_only=True, keep_links=False
    )
    xlsx_ws_list = xlsx_file.sheetnames
    for ws_name in xlsx_ws_list:
        xlsx_id = panic_handler.get_xlsx_id(input_file, ws_name)
        file_ws_dict[input_file] += [ws_name]
        ws = xlsx_file[ws_name]

        max_row = ws.max_row
        max_col = ws.max_column
        type_val_err_msg = "Provided value was invalid. Setting variable to None."
        less_than_one_msg = (
            "Provided numerical value was invalid. Counting should start at one."
        )
        while (not isinstance(max_row, int)) or (max_row <= 0):
            try:
                max_row = int(
                    panic_handler.user_input(
                        f"Max row for {xlsx_id} is {str(max_row)}.",
                        "Please provide the number of rows (starting at 1)",
                    )
                )
            except (ValueError, TypeError):
                print(
                    type_val_err_msg,
                    end="",
                    file=sys.stderr,
                )
                max_row = None
            if (isinstance(max_row, int)) and (max_row <= 0):
                print(
                    less_than_one_msg,
                    end="",
                    file=sys.stderr,
                )
        max_rows[(input_file, ws_name)] = max_row
        while (not isinstance(max_col, int)) or (max_col <= 0):
            try:
                max_col = int(
                    panic_handler.user_input(
                        f"Max col for {xlsx_id} is {str(max_col)}.",
                        "Please provide the number of columns (starting at 1)",
                    )
                )
            except (ValueError, TypeError):
                print(type_val_err_msg, end="", file=sys.stderr)
                max_col = None
            if (isinstance(max_col, int)) and (max_col <= 0):
                print(less_than_one_msg, end="", file=sys.stderr)
        max_cols[(input_file, ws_name)] = max_col
    xlsx_file.close()

# The xlsx files might have a title,
# which needs to be avoided.
min_header_rows = {}

# A row with just a title would not fill up the entire
# max_column. As a result, there would be None at either
# the first or second position.
start_title_col = 1
end_title_col = 2

# Find where headers are inside each worksheet.
for input_file in file_ws_dict:
    xlsx_file = load_workbook(
        input_file, read_only=True, keep_vba=False, data_only=True, keep_links=False
    )
    for ws_name in file_ws_dict[input_file]:
        ws = xlsx_file[ws_name]
        # Assume the first line is not title unless otherwise found out.
        header_row = 1

        for row in ws.iter_rows(
            min_row=ws.min_row,
            max_row=max_rows[(input_file, ws_name)],
            min_col=start_title_col,
            max_col=end_title_col,
            values_only=True,
        ):
            is_valid_header_row = True
            for cell in row:
                if cell is None:
                    is_valid_header_row = False
                    header_row += 1
                    break
            if is_valid_header_row:
                break
        # Only add to min_header_row if the header was found
        # and is not the only thing in object.
        if header_row < max_rows[(input_file, ws_name)]:
            # Check if there are only empty rows after header.
            post_header = header_row + 1
            row_list = []
            for row in ws.iter_rows(
                min_row=post_header,
                max_row=post_header,
                min_col=ws.min_column,
                max_col=max_cols[(input_file, ws_name)],
                values_only=True,
            ):
                for cell in row:
                    row_list += [str(cell)]
            if row_list.count("None") != len(row_list):
                min_header_rows[(input_file, ws_name)] = header_row
    xlsx_file.close()

# Check if script can be continued.
if len(min_header_rows) == 0:
    print("FE: No file contained valid headers", file=sys.stderr)
    sys.exit(2)

# Temp file list so that keys won't be deleted
# in the dictionary being parsed.
file_list = file_ws_dict.keys()

for input_file in file_list:
    is_file_used = False
    for used_file_ws in min_header_rows:
        used_file = used_file_ws[0]
        if input_file == used_file:
            is_file_used = True
            break
    if not is_file_used:
        panic_handler.panic(
            string.Template("$file contains no valid headers.").substitute(
                file=input_file
            )
        )
        del file_ws_dict[input_file]

# Make sure file_list isn't accidently used.
del file_list

for input_file in file_ws_dict:
    for ws_name in file_ws_dict[input_file]:
        is_ws_used = False
        for used_file_ws in min_header_rows:
            used_file = used_file_ws[0]
            used_ws = used_file_ws[1]
            if input_file == used_file and ws_name == used_ws:
                is_ws_used = True
                break
        if not is_ws_used:
            panic_handler.panic(
                f"{panic_handler.get_xlsx_id(input_file, ws_name)} contains no valid headers."
            )
            file_ws_dict[input_file].remove(ws_name)

# Record all headers for remaining files and worksheets.
xlsx_headers = {}
for input_file in file_ws_dict:
    xlsx_file = load_workbook(
        input_file, read_only=True, keep_vba=False, data_only=True, keep_links=False
    )
    for ws_name in file_ws_dict[input_file]:
        xlsx_headers[(input_file, ws_name)] = {}
        ws = xlsx_file[ws_name]
        # These variables are used to keep
        # track of if a valid string or int
        # appears after a set of Nones in the
        # header.
        start_none = 0
        valid_after_none = False
        for row in ws.iter_rows(
            min_row=min_header_rows[(input_file, ws_name)],
            max_row=min_header_rows[(input_file, ws_name)],
            min_col=ws.min_column,
            max_col=max_cols[(input_file, ws_name)],
            values_only=True,
        ):
            for index_cell in enumerate(row, 1):
                index = index_cell[0]
                cell = index_cell[1]
                if cell is None:
                    if start_none == 0:
                        start_none = index
                    print(
                        f"Warning: Blank header #{str(index)} in {panic_handler.get_xlsx_id(input_file, ws_name)} will be ignored",
                        file=sys.stderr,
                    )
                else:
                    if start_none != 0 and not valid_after_none:
                        valid_after_none = True
                    xlsx_headers[(input_file, ws_name)][str(cell)] = index
        if start_none and not valid_after_none:
            before_none = start_none - 1
            if before_none == 0:
                panic_handler.panic(
                    string.Template(
                        "Attempted to reduce max column length from $col to 0 in $id"
                    ).substitute(
                        col=max_cols[(input_file, ws_name)],
                        id=panic_handler.get_xlsx_id(input_file, ws_name),
                    )
                )
            else:
                print(
                    string.Template(
                        "Info: Reducing max_column length of $id from $cur_col to $new_col."
                    ).substitute(
                        id=panic_handler.get_xlsx_id(input_file, ws_name),
                        cur_col=str(max_cols[(input_file, ws_name)]),
                        new_col=str(before_none),
                    ),
                    file=sys.stderr,
                )
                max_cols[(input_file, ws_name)] = before_none
    xlsx_file.close()

# Figure out the proper mapping between Axelor CSV and xlsx.
for input_file in file_ws_dict:
    for ws_name in file_ws_dict[input_file]:
        with open(map_file) as map_fptr:
            common.map_dict[(input_file, ws_name)] = {}
            axm_line = ""
            while axm_line is not None:
                axm_line = axm_parser.get_axm_data(
                    map_fptr,
                    input_file,
                    ws_name,
                    xlsx_headers[(input_file, ws_name)],
                )
                if axm_line is not None:
                    for key in axm_line:
                        common.map_dict[(input_file, ws_name)][key] = axm_line[key]

# Convert xlsx to Axelor-compatible CSV.
invconv_logic.commit_headers()
for input_file in file_ws_dict:
    xlsx_file = load_workbook(
        input_file, read_only=True, keep_vba=False, data_only=True, keep_links=False
    )
    for ws_name in file_ws_dict[input_file]:
        ws = xlsx_file[ws_name]
        invconv_logic.file_ws_init(input_file, ws_name, max_cols[(input_file, ws_name)])

        # Use headers gathered earlier.
        for xlsx_header in xlsx_headers[(input_file, ws_name)]:
            header_index = xlsx_headers[(input_file, ws_name)][xlsx_header]
            invconv_logic.set_header_location(xlsx_header, header_index)

        # Don't need to start at header row.
        starting_row = min_header_rows[(input_file, ws_name)] + 1
        for row in ws.iter_rows(
            min_row=starting_row,
            max_row=max_rows[(input_file, ws_name)],
            min_col=ws.min_column,
            max_col=max_cols[(input_file, ws_name)],
            values_only=True,
        ):
            for index_cell in enumerate(row, 1):
                cell_index = index_cell[0]
                cell = index_cell[1]
                invconv_logic.main(cell)
    xlsx_file.close()
