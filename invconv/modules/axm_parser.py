# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

from modules import common
from modules import panic_handler
import string
import sys


def get_axm_data(axm_fptr, input_file, ws_name, input_columns):
    axm_dict = {}
    line = axm_fptr.readline().replace("\n", " ").replace(" ", "")
    if ":" in line:
        dict_key_map = line.split(":")
        dict_val = dict_key_map[1].split(",")
        valid_input_col = ""
        for possible_col in dict_val:
            for input_column in input_columns:
                if possible_col == input_column.upper():
                    valid_input_col = input_column
                    break
            if len(valid_input_col) == 0:
                for input_column in input_columns:
                    if possible_col in input_column.upper():
                        valid_input_col = input_column
                        break
        if not len(valid_input_col) == 0:
            axm_dict[dict_key_map[0]] = valid_input_col
        else:
            print(
                string.Template(
                    "FE: $header cannot be set from data in $id"
                ).substitute(
                    header=dict_key_map[0],
                    id=panic_handler.get_xlsx_id(input_file, ws_name),
                ),
                file=sys.stderr,
            )
            sys.exit(1)
    elif ">" in line:
        dict_key_equiv = line.split(">")
        if dict_key_equiv[1] in common.map_dict[(input_file, ws_name)]:
            axm_dict[dict_key_equiv[0]] = common.map_dict[(input_file, ws_name)][
                dict_key_equiv[1]
            ]
        else:
            print(
                string.Template(
                    "FE: Can't set $header to the value in $target with data from $id"
                ).substitute(
                    header=dict_key_equiv[0],
                    target=dict_key_equiv[1],
                    id=panic_handler.get_xlsx_id(input_file, ws_name),
                ),
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        return None
    return axm_dict
