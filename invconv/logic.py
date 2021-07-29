# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import csv

try:
    import axm
    import common
    import logic_func
except ModuleNotFoundError:
    import invconv.axm as axm
    import invconv.common as common
    import invconv.logic_func as logic_func

# Contains the input header
# names in their proper order.
input_header_list = []
# Keeps track of the position amongst
# the input columns
pos_index = 0


def init(file_name, section_name, header_list):
    global input_header_list
    common.file_name = file_name
    common.section_name = section_name
    input_header_list = header_list


def main(val):
    global pos_index
    str_val = ""
    if val is not None:
        # Force val to be string.
        str_val = str(val)
    for header in common.axelor_csv_columns:
        input_col = input_header_list[pos_index]
        if axm.output.is_valid_input_col(
            (common.file_name, common.section_name), header, input_col
        ):
            common.csv_row[header] = axm.output.string(
                (common.file_name, common.section_name), header, str_val
            )
    max_pos = len(input_header_list) - 1
    if pos_index == max_pos:
        pos_index = 0
        # Only commit if there is content in csv_row.
        # There won't be if a section is avoided, for instance.
        if common.csv_row:
            commit_row()
            common.row_incr += 1
        else:
            common.csv_row.clear()
    else:
        pos_index += 1


def commit_headers():
    if isinstance(common.output_file_path, str):
        with open(common.output_file_path, "a", newline="") as fptr:
            csv_out = csv.writer(fptr, dialect="excel")
            csv_out.writerow(common.axelor_csv_columns)
    else:
        csv_out = csv.writer(common.output_file_path, dialect="excel")
        csv_out.writerow(common.axelor_csv_columns)


import_id_incr = 0


def commit_row():
    global import_id_incr
    # Handle special cases.
    common.csv_row["fullName"] = (
        "[" + common.csv_row["code"] + "] " + common.csv_row["name"]
    )
    import_id_incr += 1
    common.csv_row["importId"] = import_id_incr

    # Make sure all undefined columns are blank.
    for ax_column in common.axelor_csv_columns:
        if ax_column not in common.csv_row:
            common.csv_row[ax_column] = ""

    # Enforce a consistant ordering.
    row_list = []
    for ax_column in common.axelor_csv_columns:
        row_list.append(common.csv_row[ax_column])

    if isinstance(common.output_file_path, str):
        with open(common.output_file_path, "a", newline="") as fptr:
            csv_out = csv.writer(fptr, dialect="excel")
            csv_out.writerow(row_list)
    else:
        csv_out = csv.writer(common.output_file_path, dialect="excel")
        csv_out.writerow(row_list)
    common.csv_row.clear()
