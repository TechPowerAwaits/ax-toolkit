# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD
import collections
import string

from exceptions import InvconvUnsupportedDataFile
import ini

axelor_csv_columns = {}

# Uses a meta table so that more functionality
# can be outside the script.
meta_table = {}
constants = {}
fallback = {}

# A dictionary containing
# the list of arguments to
# be parsed by the script.
arg_dict = {}
arg_tuple = collections.namedtuple("arg_tuple", ("short", "long", "help"))

# When enabled, provides extra debugging information.
is_debug = False

# Supported data file version number.
# Must be exact match.
SUPPORTED_FORMAT_VER = 4


def init(fptr):
    data_parser = ini.data_parser
    data_parser.read_file(fptr)

    global arg_dict
    global axelor_csv_columns
    global constants
    global fallback
    global meta_table

    data_format_version = data_parser.getint("INFO", "INVCONV_FORMAT")
    if data_format_version != SUPPORTED_FORMAT_VER:
        raise InvconvUnsupportedDataFile(data_format_version, SUPPORTED_FORMAT_VER)
    axelor_csv_type = data_parser["INFO"]["TYPE"]
    axcol_sect_name = string.Template("$type COLUMNS").substitute(type=axelor_csv_type)
    for key in data_parser[axcol_sect_name]:
        axelor_csv_columns[key] = data_parser[axcol_sect_name][key]
    # Add all the sections in the data file into script, irregardless
    # of type, since each section needs a unique name anyway.
    # Section names should be lowercase, but not key names.
    # That is because section names are usually all-caps, while
    # key names are case-sensitive.
    for section in data_parser.sections():
        if section != axcol_sect_name:
            meta_table[section.lower()] = {}
            for key in data_parser[section]:
                meta_table[section.lower()][key] = data_parser[section].getuni(key)
    # Deal with fallback values and constants.
    for constant_name in data_parser["CONSTANTS"]:
        if constant_name.lower() in meta_table:
            # Assume that in this case, it is a fallback
            # for something. Fallback values are always
            # a key for a section, meaning they'd always
            # be a string.
            fallback[constant_name.lower()] = data_parser["CONSTANTS"][constant_name]
            # Also deal with creating the dictionary of arguments.
            shortform_arg = data_parser["ARGUMENTS_ABREV"][constant_name]
            longform_arg = data_parser["ARGUMENTS"][constant_name]
            arg_dict[constant_name.lower()] = arg_tuple(
                short=shortform_arg,
                long=longform_arg,
                help=generate_help(constant_name),
            )
        else:
            # Since they are constants, the name of them should be all caps.
            constants[constant_name] = data_parser["CONSTANTS"].getuni(constant_name)


def generate_help(target):
    target = target.lower().replace("_", " ").title()
    return f"Overrides the fallback value for {target}"
