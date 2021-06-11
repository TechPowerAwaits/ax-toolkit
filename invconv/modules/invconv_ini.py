# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD
import configparser

data_parser = configparser.RawConfigParser(
    allow_no_value=False,
    delimiters=["="],
    comment_prefixes=["#"],
    strict=True,
    empty_lines_in_values=True,
    default_section=None,
    interpolation=None,
)
data_parser.optionxform = lambda option: option
