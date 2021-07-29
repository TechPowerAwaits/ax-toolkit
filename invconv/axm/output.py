# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

try:
    import axm.common as common
except ModuleNotFoundError:
    import invconv.axm.common as common

# Handle user-defined functions that modify input text.
_FUNCTION_MAP = {}


def get_func(outcol):
    if outcol not in _FUNCTION_MAP:
        return None
    return _FUNCTION_MAP[outcol]


def set_func(outcol, incol):
    global _FUNCTION_MAP
    _FUNCTION_MAP[outcol] = incol


# Checks if the input column name matches the valid
# input column for a given output column. If the valid input
# column is None or non-existant, the function always returns True,
# as the output string shouldn't depend on the input. This might
# cause such cases to be dealt with several times in a row (in
# the likely case that the use of string() is guarded by this
# function), but it shouldn't alter the resulting string.

# It also returns True if output_col was not defined in the axm file
# for the string() function would attempt to get a fallback value for it.
def is_valid_input_col(file_section, output_col, input_col):
    # Need to conform the file-section name sheme used internally in the script
    # to the scheme used by the AXM file.
    proper_file_section = common.get_file_sect(file_section[0], file_section[1])
    # Ensure file-section is in column_output_dict (where the strings to output
    # are located). This automatically excludes file-section pairs from the
    # avoid list.
    if proper_file_section in common.column_output_dict:
        if proper_file_section not in common.valid_col_dict:
            return True
        if output_col not in common.column_output_dict[proper_file_section]:
            return True
        if output_col not in common.valid_col_dict[proper_file_section]:
            return True
        if common.valid_col_dict[proper_file_section][output_col] is None:
            return True
        if common.valid_col_dict[proper_file_section][output_col] == input_col:
            return True
    return False


def string(file_section, output_col, input_txt):
    output_func = get_func(output_col)
    # Need to conform the file-section name sheme used internally in the script
    # to the scheme used by the AXM file.
    proper_file_section = common.get_file_sect(file_section[0], file_section[1])
    out_str = ""
    # If the file section and/or output column is missing, something must have been deleted or avoided.
    # In that case, it will attempt passing an empty quote to output_func in the hopes of
    # getting some fallback value.
    if (
        proper_file_section in common.column_output_dict
        and output_col in common.column_output_dict[proper_file_section]
    ):
        out_str = common.column_output_dict[proper_file_section][output_col]
        out_str = out_str.replace(common.INPUT_TXT_VAR, input_txt)
        # Try to pass the input_txt to output_func to get the proper output.
        # If a function is not provided, fallback to input text so that no
        # content is lost.
        if common.OUTPUT_TXT_VAR in out_str:
            if output_func is not None:
                out_str = out_str.replace(
                    common.OUTPUT_TXT_VAR, str(output_func(input_txt))
                )
            else:
                out_str = out_str.replace(common.OUTPUT_TXT_VAR, input_txt)
    else:
        if output_func is not None:
            out_str = output_func("")
    return out_str
