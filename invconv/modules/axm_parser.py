# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

from modules import common
from modules import msg_handler
import string


def get_axm_data(axm_fptr, input_file, ws_name, input_columns):
    # By default, returns None if nothing valid has been provided.
    # Otherwise, it will return a tuple. The first member of the tuple
    # is the Axelor column name while the second is the found
    # header name in the input file that can be used.
    axm_return = None
    # Convert the new line char to a space to that it will be removed
    # when the whitespace at the beginning and at the end of the string
    # is stripped.
    line = axm_fptr.readline().replace("\n", " ").lstrip().rstrip()
    # Handle comments.
    if "#" in line:
        line = split_n_strip(line, "#")
        # If the entire line is a comment,
        # split_n_strip() will return an
        # empty string in the first position
        # of the list.
        if line[0] == "":
            axm_return = (None, None)
            line = ""
        else:
            # Should give the line minus any comments.
            line = line[0]
    if ":" in line:
        key_val_map = split_n_strip(line, ":")
        ax_header = key_val_map[0]
        val_list = split_n_strip(key_val_map[1], ",")
        valid_input_col = ""
        # First, try looking for exact matches for input columns.
        # If it can't find anything, it looks for substring matches.
        for possible_col in val_list:
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
            axm_return = (ax_header, valid_input_col)
        else:
            msg_handler.error(
                string.Template("$header cannot be set from data in $id.").substitute(
                    header=ax_header,
                    id=msg_handler.get_xlsx_id(input_file, ws_name),
                )
            )
    elif ">" in line:
        key_equiv_map = split_n_strip(line, ">")
        key = key_equiv_map[0]
        source_key = key_equiv_map[1]
        if key_equiv_map[1] in common.map_dict[(input_file, ws_name)]:
            axm_return = (key, common.map_dict[(input_file, ws_name)][source_key])
        else:
            msg_handler.error(
                string.Template(
                    "Can't set $header to the value in $target with data from $id."
                ).substitute(
                    header=key,
                    target=source_key,
                    id=msg_handler.get_xlsx_id(input_file, ws_name),
                )
            )
    else:
        pass
    return axm_return


# This function acts like split(), except it removes any whitespace
# at the beginning and ends of the strings.
def split_n_strip(string, sep):
    split_list = []
    tmp_str = []
    if len(string) == 0:
        split_list += [""]
    else:
        for index_char in enumerate(string):
            index = index_char[0]
            char = index_char[1]
            if char == sep:
                if index == 0:
                    split_list += [""]
                else:
                    split_list += ["".join(tmp_str).lstrip().rstrip()]
                tmp_str.clear()
            else:
                tmp_str += char
        # Need to add all the text after the last seperator.
        split_list += ["".join(tmp_str).lstrip().rstrip()]
    return split_list
