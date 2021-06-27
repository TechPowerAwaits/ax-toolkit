# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD
import configparser

# Create getuni() method to automatically convert
# to int when appropriate. Short for universal.


def universal_get(string):
    return_val = string
    if string.isdecimal():
        return_val = int(string)
    return return_val


data_parser = configparser.RawConfigParser(
    allow_no_value=False,
    delimiters=["="],
    comment_prefixes=["#"],
    strict=True,
    empty_lines_in_values=True,
    default_section=None,
    interpolation=None,
    converters={"uni": universal_get},
)
data_parser.optionxform = lambda option: option
