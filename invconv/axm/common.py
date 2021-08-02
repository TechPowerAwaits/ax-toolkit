# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import collections
import os

try:
    from axm.exceptions import (
        AxmExpectedVarNotFound,
        AxmInvalidFileSection,
        AxmSourceNotIterable,
    )
    import axm.scheduler as scheduler
    import axm.utils as utils
except ModuleNotFoundError:
    from invconv.axm.exceptions import (
        AxmExpectedVarNotFound,
        AxmInvalidFileSection,
        AxmSourceNotIterable,
    )
    import invconv.axm.scheduler as scheduler
    import invconv.axm.utils as utils

# The file section information.
file_fallback = "common"
sect_fallback = "common"
cur_file = file_fallback
cur_sect = sect_fallback
used_files = [file_fallback]
used_sect = [sect_fallback]

### Default lists and dictionaries used with axm. ###

# Stores all the optional variables for each file and section.
opt_dict = {}

# Maps between the output column name and the possible input column names.
# Indexed by (filename, sectionname).
out_input_col = {}

# For each file-section and for every output_column, it stores what text
# should be printed.
column_output_dict = {}

# Stores what variables should be removed for each file and section.
del_dict = {}

# List of files and sections to avoid
avoid_list = []

# Input column dictionary
# Stores all the input columns indexed by (filename, sectionname).
input_col_dict = {}

# The major version of the version number in both SUPPORTED_AXM_VER
# and the axm file itself must be an exact match. For the minor version
# number, the one in the axm file must be less than or equal to the one
# in SUPPORTED_AXM_VER.
_tmp_ver_tuple = collections.namedtuple("ver_tuple", ("major", "minor"))


class ver_tuple(_tmp_ver_tuple):
    def __str__(self):
        return str(self.major) + "." + str(self.minor)


SUPPORTED_AXM_VER = ver_tuple(3, 2)
# Only need to check the version once.
version_checked = False

# Contains the valid input column found or None
# for each axelor column name inside a file-section pair.
valid_col_dict = {}

# Adds more specific file-section pairs to list/dictionary if a
# generic file-section pair is found. For example, if (file, common)
# is found, (file, super_section) might be added.
def specialize(table):
    generic_file_section_list = []
    # Setting the sources in here in order to ensure all the sources have
    # been populated (avoiding a race condition). The sources might be set
    # multiple times, but since it uses a set, it won't have duplicates.
    join_list = list(out_input_col.keys())
    join_list.extend(list(column_output_dict.keys()))
    # A joined list is used as opposed to specifying both sources
    # seperately because a valid axm mapping file might fill out_input_col
    # and not column_output_dict and vice versa.
    set_file_section_source(join_list)
    file_section_set = get_file_section_set()
    # Since this is a more generic function,
    # need to check whether table is dict or list.
    # If it is a dict, need to know what should be inside it.
    table_type = utils.get_table_type(table)

    for file_section_pair in table:
        section_name = file_section_pair[1]
        if section_name == sect_fallback:
            generic_file_section_list.append(file_section_pair)
    # If (common, common) is in generic list, add all possible
    # file-section pairs.
    if (file_fallback, sect_fallback) in generic_file_section_list:
        for file_section_pair in file_section_set:
            if (
                file_section_pair != (file_fallback, sect_fallback)
                and file_section_pair not in table
                and file_section_pair not in avoid_list
            ):
                if table_type == "list":
                    table.append(file_section_pair)
                elif table_type == "dict":
                    table[file_section_pair] = None
                elif table_type == "dict-list":
                    table[file_section_pair] = []
                elif table_type == "dict-dict":
                    table[file_section_pair] = {}
                else:
                    pass
    # For other cases, add the more specific file-section pairs
    # for the specialized file sections.
    elif len(generic_file_section_list) > 0:
        for generic_file_section_pair in generic_file_section_list:
            generic_file_name = generic_file_section_pair[0]
            for file_section_pair in file_section_set:
                file_name = file_section_pair[0]
                if (
                    file_section_pair != generic_file_section_pair
                    and file_name == generic_file_name
                    and file_section_pair not in table
                    and file_section_pair not in avoid_list
                ):
                    if table_type == "list":
                        table.append(file_section_pair)
                    elif table_type == "dict":
                        table[file_section_pair] = None
                    elif table_type == "dict-list":
                        table[file_section_pair] = []
                    elif table_type == "dict-dict":
                        table[file_section_pair] = {}
                    else:
                        pass
    else:
        pass


# There are many lists and dictionaries which use the inherit function,
# hence why it is in common.
def inherit(table):
    for file_section in table:
        file_name = file_section[0]
        section_name = file_section[1]
        # There is nothing to inherit if the file-section pair is already
        # the most generic or if something more generic doesn't exist.
        if (
            file_name != file_fallback
            and section_name != sect_fallback
            and (file_name, sect_fallback) in table
        ):
            for item in table[(file_name, sect_fallback)]:
                if item not in table[file_section]:
                    if isinstance(table[file_section], list):
                        table[file_section].append(item)
                    if isinstance(table[file_section], dict):
                        table[file_section][item] = table[(file_name, sect_fallback)][
                            item
                        ]
    # Depending on how the axm file was written, the most
    # generic (file_fallback, sect_fallback) might not
    # exist.
    if (file_fallback, sect_fallback) in table:
        for item in table[(file_fallback, sect_fallback)]:
            for file_section in table:
                if file_section != (file_fallback, sect_fallback):
                    if item not in table[file_section]:
                        if isinstance(table[file_section], list):
                            table[file_section].append(item)
                        if isinstance(table[file_section], dict):
                            table[file_section][item] = table[
                                (file_fallback, sect_fallback)
                            ][item]


# This function is a helper function for get_file_name()
# and others like that. It returns the available
# file section pairs from multiple sources and places
# it in a set (so there won't be any duplicates).
_file_section_set = set()


def set_file_section_source(*sources):
    # Any sources used must be interable.
    for source in sources:
        # Technically, an empty iterable object is still
        # iterable, but for all practical purposes, it is
        # probably not wanted nor expected.
        if hasattr(source, "__iter__") and len(source) > 0:
            _file_section_set.update(source)
        else:
            raise AxmSourceNotIterable(source)


def get_file_section_set():
    return _file_section_set


# References to filenames in the axm file
# might not be an absolute value. It could
# simply be just the base filename or a relative path.
def get_file_name(file_name):
    return_name = ""
    # The avoid_list needs to be added to the file_section
    # sources in order to be able to convert the non
    # axm file-section pairs to the axm file-section pairs.
    # That way, everything in the avoid list can be
    # dealt with appropriately. Only do so if the avoid_list
    # is not empty.
    if avoid_list:
        set_file_section_source(avoid_list)
    file_section_set = get_file_section_set()

    for file_section in file_section_set:
        axm_file_name = file_section[0]
        if (
            file_name == axm_file_name
            or os.path.abspath(file_name) == axm_file_name
            or os.path.relpath(file_name) == axm_file_name
            or os.path.basename(file_name) == axm_file_name
        ):
            return_name = axm_file_name
            break
    # Test out file_name without file extension.
    if (file_ext_pos := file_name.rfind(".")) != -1 and len(return_name) == 0:
        max_pos = len(file_name) - 1
        # Don't bother checking for file extension if filename
        # is one character long or file_ext_pos wasn't found.
        if max_pos > 0:
            incr = file_ext_pos
            tmp_list = list(file_name)
            tmp_str = ""
            while incr <= max_pos:
                del tmp_list[file_ext_pos]
                incr += 1
            tmp_str = "".join(tmp_list)
            return get_file_name(tmp_str)
    return return_name


# Sections have to be an exact match (case sensitive).
# Exceptions are made for whitespace at the beginning and end
# of section names.
def get_sect_name(sect_name):
    return_name = ""
    file_section_set = get_file_section_set()

    for file_section in file_section_set:
        axm_sect_name = file_section[1]
        if sect_name == axm_sect_name:
            return_name = axm_sect_name
            break
    if len(return_name) == 0:
        strip_sect_name = sect_name.strip()
        # Only run the function again if
        # the strip_sect_name is distinct from
        # the original sect_name. Helps prevent
        # an infinite loop.
        if strip_sect_name != sect_name:
            return get_sect_name(strip_sect_name)
    return return_name


# Handles both file and section names, and additionally,
# checks if the file and section names are in the same
# tuple.
def get_file_sect(file_name, section_name):
    axm_file_name = get_file_name(file_name)
    if len(axm_file_name) == 0:
        axm_file_name = file_fallback
    axm_sect_name = get_sect_name(section_name)
    if len(axm_sect_name) == 0:
        axm_sect_name = sect_fallback
    file_section = (axm_file_name, axm_sect_name)

    file_section_set = get_file_section_set()
    # Try to find a fallback file_section before returning None.
    if file_section not in file_section_set:
        if (axm_file_name, sect_fallback) in file_section_set:
            file_section = (axm_file_name, sect_fallback)
        elif (file_fallback, sect_fallback) in file_section_set:
            file_section = (file_fallback, sect_fallback)
        else:
            file_section = None
    return file_section


def prep_valid_col_dict():
    global valid_col_dict
    # The given file and section name might be different
    # from what is used in the AXM file, since a file extension
    # might be missing, and as well, the axm file doesn't usually
    # include the path to the file which is what the given file name
    # almost always give.
    for file_name, section_name in input_col_dict.keys():
        proper_file_section = get_file_sect(file_name, section_name)
        if proper_file_section not in avoid_list:
            if proper_file_section not in out_input_col:
                raise AxmInvalidFileSection(file_name, section_name)
            # Have values invalid_col_dict default to None
            # if no valid input column is found.
            if proper_file_section not in valid_col_dict:
                valid_col_dict[proper_file_section] = {}
            for output_col in out_input_col[proper_file_section]:
                if output_col not in valid_col_dict[proper_file_section]:
                    valid_col_dict[proper_file_section][output_col] = None


# For the more generic file-section pairs,
# if they are actually used, it is assumed
# that all of them would have the same valid
# input col. So, nothing is stopping a
# generic file-section pair from being
# evaluated multiple times, as it shouldn't
# produce a different valid input column.
def find_valid_col():
    global valid_col_dict
    for file_section in input_col_dict:
        file_name = file_section[0]
        section_name = file_section[1]
        # The given file and section name might be different
        # from what is used in the AXM file, since a file extension
        # might be missing, and as well, the axm file doesn't usually
        # include the path to the file which is what the given file name
        # almost always give.
        proper_file_section = get_file_sect(file_name, section_name)
        if proper_file_section in valid_col_dict:
            valid_input_cols = input_col_dict[file_section]
            # Contains the input columns axm is looking for in a dictionary
            # indexed by output col.
            possible_input_dict = out_input_col[proper_file_section]
            for output_col in valid_col_dict[proper_file_section]:
                # Do everything starting in terms of possible_input_cols, as the
                # ordering of that list is canonical.
                possible_input_cols = possible_input_dict[output_col]
                for possible_input_col in possible_input_cols:
                    # First, test all possible input columns for exact input column matches.
                    # (Keeping in mind that the possible input columns are all caps.)
                    for valid_input_col in valid_input_cols:
                        if (
                            valid_input_col.upper() == possible_input_col
                            and valid_col_dict[proper_file_section][output_col] is None
                        ):
                            valid_col_dict[proper_file_section][
                                output_col
                            ] = valid_input_col
                    # Then, try to find possible_col within input_col.
                    for valid_input_col in valid_input_cols:
                        if (
                            possible_input_col in valid_input_col.upper()
                            and valid_col_dict[proper_file_section][output_col] is None
                        ):
                            valid_col_dict[proper_file_section][
                                output_col
                            ] = valid_input_col


# Remove all file-section pairs and variables that
# are optional, avoided, etc.
def purge_valid_col():
    global valid_col_dict
    # Handle the avoid_list.
    for avoid_file_section in avoid_list:
        if avoid_file_section in valid_col_dict:
            del valid_col_dict[avoid_file_section]
    # Handle the del_dict.
    for file_section in del_dict:
        if file_section in valid_col_dict:
            for out_col in del_dict[file_section]:
                if out_col in valid_col_dict:
                    del valid_col_dict[file_section][out_col]
    # Handle the opt_dict.
    # Remove those optional variables that are None.
    for file_section in opt_dict:
        if file_section in valid_col_dict:
            for out_col in opt_dict[file_section]:
                if out_col in valid_col_dict and out_col is None:
                    del valid_col_dict[file_section][out_col]
    # Remove more generic file-section pairs if they weren't
    # used except for inheritance.
    used_generic_file_section = []
    for file_name, sect_name in input_col_dict.keys():
        proper_file_section = get_file_sect(file_name, sect_name)
        proper_section_name = proper_file_section[1]
        if proper_file_section is not None and proper_section_name == sect_fallback:
            used_generic_file_section.append(proper_file_section)
    # Compare the actually used generic file section list to
    # the file sections actually used in valid_input_col.
    # and remove if not used. If it is not removed,
    # check_valid_col() might fail and complain about it.
    for file_section in valid_col_dict:
        section_name = file_section[1]
        if (
            section_name == sect_fallback
            and file_section not in used_generic_file_section
        ):
            del valid_col_dict[file_section]


# Check if mapping in valid_col_dict is None and has no excuse.
def check_valid_col():
    # Will be passed to exception
    # if not empty.
    missing_map_dict = {}
    for file_section in valid_col_dict:
        for output_col in valid_col_dict[file_section]:
            # All excusable missing mappings have already
            # been removed in purge_valid_col().
            if valid_col_dict[file_section][output_col] is None:
                if file_section not in missing_map_dict:
                    missing_map_dict[file_section] = []
                missing_map_dict[file_section].append(output_col)
    if missing_map_dict:
        raise AxmExpectedVarNotFound(missing_map_dict)


scheduler.add(prep_valid_col_dict, scheduler.NICE_VALID_COL)
scheduler.add(find_valid_col, scheduler.NICE_VALID_COL)
scheduler.add(purge_valid_col, scheduler.NICE_VALID_COL)
scheduler.add(check_valid_col, scheduler.NICE_VALID_COL)

INPUT_COL_VAR = "$input_col"
OUTPUT_COL_VAR = "$output_col"
INPUT_TXT_VAR = "$input_txt"
OUTPUT_TXT_VAR = "$output_txt"


def set_output():
    global column_output_dict
    for file_section in valid_col_dict:
        if file_section not in column_output_dict:
            column_output_dict[file_section] = {}
        for output_col in valid_col_dict[file_section]:
            if output_col in column_output_dict[file_section]:
                column_output_dict[file_section][output_col] = (
                    column_output_dict[file_section][output_col]
                    .replace(INPUT_COL_VAR, valid_col_dict[file_section][output_col])
                    .replace(OUTPUT_COL_VAR, output_col)
                )
            else:
                column_output_dict[file_section][output_col] = OUTPUT_TXT_VAR


scheduler.add(set_output, scheduler.NICE_OUT_STRING)
