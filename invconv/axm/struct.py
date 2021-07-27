# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import collections

try:
    import axm.common as common
    from axm.exceptions import AxmNameExists, AxmInvalidName
    import axm.utils as utils
except ModuleNotFoundError:
    import invconv.axm.common as common
    from invconv.axm.exceptions import AxmNameExists, AxmInvalidName
    import invconv.axm.utils as utils

struct_tuple = collections.namedtuple("struct_tuple", ("check_func", "parse_func"))

# Floats in the axm language are internally a modified namedtuple.
_tmp_float_tuple = collections.namedtuple("float_tuple", ("whole", "remainder"))


class float_tuple(_tmp_float_tuple):
    def __float__(self):
        return float(self.__str__())

    def __str__(self):
        return str(self.whole) + "." + str(self.remainder)


# This dictionary contains all valid structures.
# New structs can easily be added.
_struct_dict = {}
ALL_STRUCTS = "*"


def add(name, check_func, parse_func):
    global _struct_dict
    if name == ALL_STRUCTS:
        raise AxmInvalidName(name)
    if name in _struct_dict:
        raise AxmNameExists(name)
    _struct_dict[name] = struct_tuple(check_func, parse_func)


def get(name):
    if name == ALL_STRUCTS:
        return _struct_dict.values()
    if name in _struct_dict:
        return _struct_dict[name]
    return None


def check_exists(test_str):
    for name_tuple in _struct_dict.items():
        if name_tuple[1](test_str):
            return True
    return False


###    The basic structs available with axm and supporting functions.    ###

# Add a float struct.
# (Internally, it is represented as a tuple of integers
# for maximum flexibility. Otherwise, version 3.10 will be
# the same as version 3.1.)


def _check_float(line):
    # Need to ensure there is only one dot in float.
    if line.count(".") == 1:
        test_line = line.replace(".", "")
        if test_line.isdigit():
            return True
    return False


def _parse_float(line):
    if _check_float(line):
        tmp_list = utils.split_n_strip(line, ".")
        tuple_impl = float_tuple(whole=int(tmp_list[0]), remainder=int(tmp_list[1]))
        return tuple_impl
    return None


if get("float") is None:
    add("float", _check_float, _parse_float)


def _check_sect(line):
    # Ensure there is only one beginning and closing
    # square bracket.
    if line.count("[") == 1 and line.count("]") == 1:
        start_bracket = line.find("[")
        # Lists are easier to manipulate than strings.
        tmp_list = list(line)
        # Remove all values before and including the start_bracket
        # to ensure that all the values required are inside the square
        # brackets.
        incr = 0
        while incr <= start_bracket:
            del tmp_list[0]
            incr += 1
        # Calculate where end bracket is and remove it and values past it.
        end_bracket = tmp_list.index("]")
        tmp_list_len = len(tmp_list)
        incr = end_bracket
        while incr < tmp_list_len:
            del tmp_list[end_bracket]
            incr += 1
        tmp_str = "".join(tmp_list)
        # Make sure Section isn't by itself,
        # as file is always manditory.
        if "SECTION:" in tmp_str and "FILE:" in tmp_str:
            # File and section are always seperated by a comma.
            if tmp_str.count(",") >= 1:
                return True
        if "FILE:" in tmp_str:
            return True
    return False


def _parse_sect(line):
    file_section = (None, None)
    if _check_sect(line):
        # Starts with and ends with strip() in order to make sure the
        # prefixes and suffixes get removed properly and any spaces between
        # the square brackets and the actual content also get removed.
        tmp_line = line.strip().removeprefix("[").removesuffix("]").strip()
        # The file name is always in the first position and
        # an optional "SECTION" section entry can be added,
        # seperated by a comma. However, both filenames and
        # section names can contain commas, which requires careful
        # parsing.
        sect_pos = tmp_line.find("SECTION:")
        if sect_pos == -1:
            # Don't need to worry about section.
            file_section = (
                tmp_line.removeprefix("FILE:").lstrip(),
                common.sect_fallback,
            )
        else:
            # Lists are easier to manipulate than string.
            tmp_file_list = list(tmp_line)
            tmp_sect_list = list(tmp_line)
            incr = sect_pos
            max_pos = len(tmp_line) - 1
            # Remove the section related
            # parts from the file list.
            while incr <= max_pos:
                del tmp_file_list[sect_pos]
                incr += 1
            # Remove the file related parts
            # from the section list.
            pre_sect_pos = sect_pos - 1
            incr = 0
            while incr <= pre_sect_pos:
                del tmp_sect_list[0]
                incr += 1
            # Remove uneeded values and convert to string.
            file_name = (
                "".join(tmp_file_list)
                .rstrip()
                .removesuffix(",")
                .rstrip()
                .removeprefix("FILE:")
                .lstrip()
            )
            section_name = "".join(tmp_sect_list).removeprefix("SECTION:").strip()
            file_section = (file_name, section_name)
    return file_section


if get("sect") is None:
    add("sect", _check_sect, _parse_sect)
