# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import collections

import axm.common
from axm.exceptions import (
    axm_command_not_recognized,
    axm_invalid_command_syntax,
    axm_invalid_ver,
    axm_name_exists,
    axm_unexpected_command,
)
import axm.scheduler
import axm.struct

command_tuple = collections.namedtuple(
    "command_tuple", ("name", "check_func", "action_func")
)

# Confirms whether a operator exists in
# a string. It is generic and doesn't check
# whether the operator is being used properly
# (as opposed to check_func in command_tuple).
# It does check, however, whether it is indeed
# a registered operator.
def verify(line):
    # Remove whitespace from beginning.
    test_string = line.lstrip()
    for command in get(ALL_COMMANDS):
        if COMMAND_PREFIX + command.name in test_string:
            return True
    if test_string[0] == "!":
        # Need to convert str to deque
        # to manipulate it in order to get
        # command name.
        tmp_deque = collections.deque(test_string)
        whitespace_pos = test_string.find(" ")
        if whitespace_pos != -1:
            incr = whitespace_pos
            str_len = len(test_string)
            while incr < str_len:
                del tmp_deque[whitespace_pos]
                incr += 1
        else:
            # Since the command could not be
            # correctly parsed, put the entire
            # line as the command line (surrounded
            # by quotes). To make it easier to surround
            # it in quotes, that is why a deque was used
            # instead of a list.
            tmp_deque.appendleft('"')
            tmp_deque.append('"')
        command_name = "".join(tmp_deque)
        raise axm_command_not_recognized(command_name)
    return False


# Commands can change the target
# file and section (usually axm.common).
# They can modify dictionaries and
# variables, but they never directly
# modify strings.

COMMAND_PREFIX = "!"
_command_list = []
ALL_COMMANDS = "*"


def add(name, check_func, action_func):
    global _command_list
    name = name.upper().removeprefix(COMMAND_PREFIX)
    for item in _command_list:
        if item.name == name:
            raise axm_name_exists(name)
    _command_list.append(command_tuple(name, check_func, action_func))


def get(name):
    name = name.upper().removeprefix(COMMAND_PREFIX)
    if name == ALL_COMMANDS:
        return _command_list
    for item in _command_list:
        if item.name == name:
            return item
    return None


###    The basic commands available with axm and supporting functions.    ###

# Checks the version of the axm file.
def _check_axm(line):
    test_line = line.lstrip()
    if COMMAND_PREFIX + "AXM" in test_line:
        test_line = test_line.replace(COMMAND_PREFIX + "AXM", "").lstrip()
        # Must have a float.
        if axm.struct.get("float").check_func(test_line):
            return True
        # It must have invalid syntax.
        raise axm_invalid_command_syntax(COMMAND_PREFIX + "AXM")
    return False


def _act_axm(line):
    if _check_axm(line) and not axm.common.version_checked:
        stripped_line = line.replace(COMMAND_PREFIX + "AXM", "").lstrip()
        ver_float = axm.struct.get("float").parse_func(stripped_line)
        major_ver = ver_float.whole
        minor_ver = ver_float.remainder
        if (
            minor_ver > axm.common.SUPPORTED_AXM_VER.minor
            and not major_ver == axm.common.SUPPORTED_AXM_VER.major
        ):
            axm_invalid_ver(str(ver_float), str(axm.common.SUPPORTED_AXM_VER))
            axm.common.version_checked = True
    else:
        raise axm_unexpected_command(COMMAND_PREFIX + "AXM")


if get("AXM") is None:
    add("AXM", _check_axm, _act_axm)

# Sets the current target file and section.
def _check_sect(line):
    test_line = line.lstrip()
    if COMMAND_PREFIX + "SECT" in test_line:
        test_line.replace(COMMAND_PREFIX + "SECT", "").lstrip()
        if axm.struct.get("sect").check_func(test_line):
            return True
        # It must have invalid syntax.
        raise axm_invalid_command_syntax(COMMAND_PREFIX + "SECT")
    return False


def _act_sect(line):
    if not _check_sect(line):
        axm_unexpected_command(COMMAND_PREFIX + "SECT")
    stripped_line = line.replace(COMMAND_PREFIX + "SECT", "").lstrip()
    file_section_tuple = axm.struct.get("sect").parse_func(stripped_line)
    axm.common.cur_file = file_section_tuple[0]
    axm.common.cur_sect = file_section_tuple[1]


if get("SECT") is None:
    add("SECT", _check_sect, _act_sect)


# Marks a variable for deletion in a certain file and section.
# It doesn't remove the content right away, because due to the
# way the parser.finalize() function works, removed variables might
# be added back into the file-section pair if it exists in a more generic
# pair.

# For example, if "name" is deleted from the section [FILE: My File, SECTION: My Section],
# if it already exists in [FILE: My File], it will be readded when all children file-section pairs
# recieve data from the parent.


def _check_del(line):
    test_line = line.lstrip()
    if COMMAND_PREFIX + "DEL" in test_line:
        test_line.replace(COMMAND_PREFIX + "DEL", "").lstrip()
        # The !DEL command only supports variables.
        # Therefore, if a struct is found matching whats in the line,
        # then there is a syntax error.
        for struct_types in axm.struct.get(axm.struct.ALL_STRUCTS):
            if struct_types.check_func(test_line):
                raise axm_invalid_command_syntax(COMMAND_PREFIX + "DEL")
        return True
    return False


def _act_del(line):
    if _check_del(line):
        col_name = line.replace(COMMAND_PREFIX + "DEL", "").lstrip()
        cur_file_sect = (axm.common.cur_file, axm.common.cur_sect)
        if cur_file_sect not in axm.common.del_dict:
            axm.common.del_dict[cur_file_sect] = []
        cur_file_generic_sect = (axm.common.cur_file, axm.common.sect_fallback)
        generic_file_sect = (axm.common.file_fallback, axm.common.sect_fallback)
        # Need to check if the variable to be deleted actually exists.
        # This command will be run before anything is inherited, so checking
        # more generic file-section pairs is required.
        file_sect_list = [cur_file_sect, cur_file_generic_sect, generic_file_sect]
        col_exists = False
        for file_section in file_sect_list:
            if (
                file_section in axm.common.out_input_col
                and col_name in axm.common.out_input_col[file_section]
            ) or (
                file_section in axm.common.column_output_dict
                and col_name in axm.common.column_output_dict[file_section]
            ):
                axm.common.del_dict[cur_file_sect].append(col_name)
                col_exists = True
                break
        if not col_exists:
            # The variable it is try to delete does not exists.
            raise axm_unexpected_command(COMMAND_PREFIX + "DEL")


# Actually removes the variables marked for deletion.
def _post_del():
    for file_section in axm.common.del_dict:
        if file_section in axm.common.out_input_col:
            for output_col in axm.common.del_dict[file_section]:
                if output_col in axm.common.out_input_col[file_section]:
                    del axm.common.out_input_col[file_section][output_col]
            if len(axm.common.out_input_col[file_section]) == 0:
                # Add to avoid_list so that section can be removed
                # later.
                axm.common.avoid_list.append(file_section)


if get("DEL") is None:
    add("DEL", _check_del, _act_del)
    axm.scheduler.add(
        axm.common.specialize, axm.scheduler.NICE_INHERIT, [axm.common.del_dict]
    )
    axm.scheduler.add(
        axm.common.inherit, axm.scheduler.NICE_INHERIT, [axm.common.del_dict]
    )
    axm.scheduler.add(_post_del, axm.scheduler.NICE_DEL_N_AVOID)

# Similar to the !DEL command, except works on sect structures.
def _check_avoid(line):
    test_line = line.lstrip()
    if COMMAND_PREFIX + "AVOID" in test_line:
        test_line = test_line.replace(COMMAND_PREFIX + "AVOID", "").lstrip()
        if axm.struct.get("sect").check_func(test_line):
            return True
        # The !AVOID command requires the sect structure.
        raise axm_invalid_command_syntax(COMMAND_PREFIX + "AVOID")
    return False


def _act_avoid(line):
    if not _check_avoid(line):
        axm_unexpected_command(COMMAND_PREFIX + "AVOID")
    stripped_line = line.replace(COMMAND_PREFIX + "AVOID", "").lstrip()
    file_section_tuple = axm.struct.get("sect").parse_func(stripped_line)
    axm.common.avoid_list.append(file_section_tuple)


# Actually removes the sections from the provided list/dictionary.
def _post_avoid(table):
    for section in axm.common.avoid_list:
        if section in table:
            if isinstance(table, list):
                # It is possible that there are multiple
                # entries for the same section in a given list.
                while section in table:
                    table.remove(section)
            if isinstance(table, dict):
                del table[section]


if get("AVOID") is None:
    add("AVOID", _check_avoid, _act_avoid)
    axm.scheduler.add(
        axm.common.specialize, axm.scheduler.NICE_INHERIT, [axm.common.avoid_list]
    )
    axm.scheduler.add(
        _post_avoid, axm.scheduler.NICE_DEL_N_AVOID, [axm.common.out_input_col]
    )
    axm.scheduler.add(
        _post_avoid, axm.scheduler.NICE_DEL_N_AVOID, [axm.common.opt_dict]
    )
