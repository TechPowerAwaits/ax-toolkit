# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import argparse
from openpyxl import load_workbook
import os.path
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

file_section_ids = []
# The xlsx files might have a title,
# which needs to be avoided.
header_row = {}

for input_file in input_files:
    # Simply test that all the files specified exist
    # and create ID for each one.
    xlsx_file = load_workbook(
        input_file, read_only=True, keep_vba=False, data_only=True, keep_links=False
    )
    name_col_index = -1
    file_section_index = 0
    for ws_name in xlsx_file.sheetnames:
        file_section_ids += [input_file + " WS: " + ws_name]
    file_section_index = file_section_index + 1
    xlsx_file.close()

# On some xlsx files, the max_row and max_col
# cannot be read.
max_rows = {}
max_cols = {}
file_section_incr = 0

for input_file in input_files:
    xlsx_file = load_workbook(
        input_file, read_only=True, keep_vba=False, data_only=True, keep_links=False
    )
    for ws in xlsx_file.worksheets:
        file_section_id = file_section_ids[file_section_incr]

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
                        f"Max row for {file_section_id} is {str(max_row)}.",
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
        max_rows[file_section_id] = max_row
        while (not isinstance(max_col, int)) or (max_col <= 0):
            try:
                max_col = int(
                    panic_handler.user_input(
                        f"Max col for {file_section_id} is {str(max_col)}.",
                        "Please provide the number of columns (starting at 1)",
                    )
                )
            except (ValueError, TypeError):
                print(type_val_err_msg, end="", file=sys.stderr)
                max_col = None
            if (isinstance(max_col, int)) and (max_col <= 0):
                print(less_than_one_msg, end="", file=sys.stderr)
        max_cols[file_section_id] = max_col
        file_section_incr += 1
    xlsx_file.close()


# A row with just a title would not fill up the entire
# max_column. As a result, there would be None at either
# the first or second position.
start_title_col = 1
end_title_col = 2

# Find where columns are and figure out the proper mapping
# between Axelor CSV and xlsx.
file_section_incr = 0
xlsx_headers = {}
for input_file in input_files:
    xlsx_file = load_workbook(
        input_file, read_only=True, keep_vba=False, data_only=True, keep_links=False
    )
    for ws in xlsx_file.worksheets:
        file_section_id = file_section_ids[file_section_incr]
        # Assume the first line is not title unless otherwise found out.
        header_row[file_section_id] = 1

        for row in ws.iter_rows(
            min_row=ws.min_row,
            max_row=max_rows[file_section_id],
            min_col=start_title_col,
            max_col=end_title_col,
            values_only=True,
        ):
            is_valid_header_row = True
            for cell in row:
                if cell is None:
                    is_valid_header_row = False
                    header_row[file_section_id] = header_row[file_section_id] + 1
                    break
            if is_valid_header_row:
                break
        if header_row[file_section_id] > max_rows[file_section_id]:
            print(
                "FE: Can't find headers in {file_section_id}",
                file=sys.stderr,
            )
            sys.exit(1)
        xlsx_headers[file_section_id] = []
        for line in ws.iter_rows(
            min_row=header_row[file_section_id],
            max_row=header_row[file_section_id],
            min_col=ws.min_column,
            max_col=max_cols[file_section_id],
        ):
            for header in line:
                xlsx_headers[file_section_id] += [header.value]
        with open(map_file) as map_fptr:
            common.map_dict[file_section_id] = {}
            while True:
                axm_line = axm_parser.get_axm_data(
                    map_fptr,
                    file_section_id,
                    xlsx_headers[file_section_id],
                )
                if axm_line is not None:
                    for key in axm_line:
                        common.map_dict[file_section_id][key] = axm_line[key]
                else:
                    break
        file_section_incr += 1
    xlsx_file.close()

file_section_incr = 0
invconv_logic.commit_headers()
for input_file in input_files:
    xlsx_file = load_workbook(
        input_file, read_only=True, keep_vba=False, data_only=True, keep_links=False
    )
    for ws in xlsx_file.worksheets:
        file_section_id = file_section_ids[file_section_incr]
        invconv_logic.file_ws_init(file_section_id, max_cols[file_section_id])

        # Use headers gathered earlier.
        for index_xlsx_header in enumerate(xlsx_headers[file_section_id], 1):
            header_index = index_xlsx_header[0]
            xlsx_header = index_xlsx_header[1]
            invconv_logic.set_header_location(xlsx_header, header_index)

        # Don't need to start at header row.
        starting_row = header_row[file_section_id] + 1
        for row in ws.iter_rows(
            min_row=starting_row,
            max_row=max_rows[file_section_id],
            min_col=ws.min_column,
            max_col=max_cols[file_section_id],
            values_only=True,
        ):
            for index_cell in enumerate(row, 1):
                cell_index = index_cell[0]
                cell = index_cell[1]
                invconv_logic.main(cell)
        file_section_incr += 1
    xlsx_file.close()
