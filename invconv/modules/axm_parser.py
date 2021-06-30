# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import math
from modules import msg_handler
import os.path
import string

# Python does not have a function to check
# if a file has reached EOF. This function works
# by checking the stream position. If the position
# stops increasing, it has reached EOF.
stream_pos = None


def is_eof(axm_fptr):
    global stream_pos
    cur_pos = axm_fptr.tell()
    if stream_pos is None:
        # Initialize stream_pos.
        stream_pos = cur_pos
    else:
        if cur_pos == stream_pos:
            return True
    # Set stream_pos to cur_pos
    # or face infinite loop.
    stream_pos = cur_pos
    return False


# Common function for the is_*
# operator type confirming
# functions.
def check_oper_common(line, oper_loc):
    pre_oper_loc = oper_loc - 1
    post_oper_loc = oper_loc + 1
    # If there are other symbols
    # beside the one already found,
    # it is likely not the expected
    # operator. Rather, it would be
    # some sort of multi-character operator.
    if not (
        line[pre_oper_loc] in string.punctuation
        and line[post_oper_loc] in string.punctuation
    ):
        return True
    return False


ASSIGN_SYMBOL = ":"


def is_assign(line):
    assign_loc = line.find(ASSIGN_SYMBOL)
    line_max_index = len(line) - 1
    # The assignment operator cannot be at the first
    # or last position in a line.
    if line_max_index > assign_loc > 0:
        return check_oper_common(line, assign_loc)
    return False


def parse_assign(line):
    return_tuple = (None, None)
    if is_assign(line):
        ax_input_map = split_n_strip(line, ASSIGN_SYMBOL)
        axelor_col_name = ax_input_map[0]
        input_col_names = split_n_strip(ax_input_map[1], ",")
        return_tuple = (axelor_col_name, input_col_names)
    return return_tuple


DELEGATOR_SYMBOL = ">"


def is_delegator(line):
    delegator_loc = line.find(DELEGATOR_SYMBOL)
    line_max_index = len(line) - 1
    # The assignment operator cannot be at the first
    # or last position in a line.
    if line_max_index > delegator_loc > 0:
        return check_oper_common(line, delegator_loc)
    return False


def parse_delegator(line):
    return_tuple = (None, None)
    if is_delegator(line):
        ax_equiv_map = split_n_strip(line, DELEGATOR_SYMBOL)
        ax_dest = ax_equiv_map[0]
        ax_sources = split_n_strip(ax_equiv_map[1], ",")
        # Try to get the input column that each source in ax_sources
        # uses; else, add None to the list of input columns.
        input_col_names = []
        for source in ax_sources:
            if source in ax_inputcol_dict[(cur_file, cur_sect)]:
                input_col_names += ax_inputcol_dict[(cur_file, cur_sect)][source][0]
            elif source in ax_inputcol_dict[(cur_file, sect_fallback)]:
                input_col_names += ax_inputcol_dict[(cur_file, sect_fallback)][0]
            elif source in ax_inputcol_dict[(file_fallback, sect_fallback)]:
                input_col_names += [
                    ax_inputcol_dict[(file_fallback, sect_fallback)][source][0]
                ]
            else:
                input_col_names += [None]
        return_tuple = (ax_dest, input_col_names)
    return return_tuple


def is_sect(line):
    # Some section definitions also include a "SECTION" entry,
    # only the square brackets and "FILE:" are absolutely
    # required.
    return line.startswith("[") and line.endswith("]") and "FILE:" in line


def parse_sect(line):
    return_tuple = (None, None)
    if is_sect(line):
        tmp_line = line.removeprefix("[").removesuffix("]")
        file_section = split_n_strip(tmp_line, ",")
        file_name = file_section[0]
        section_name = file_section[1]
        # Use strip() to remove any extra spaces after "FILE:".
        file_name = file_name.removeprefix("FILE:").strip()
        # While file is required by the sect structure, section is optional.
        # When section is not provided, it defaults to common.
        if len(section_name) > 0:
            section_name = section_name.removeprefix("SECTION:").strip()
        else:
            section_name = sect_fallback
        return_tuple = (file_name, section_name)
    return return_tuple


# axm supports different structure and operator types.
# Structures are parsed after commands or
# as part of commands.
oper_types = {
    "assign": (is_assign, parse_assign),
    "delegator": (is_delegator, parse_delegator),
}
struct_types = {"sect": (is_sect, parse_sect)}


# Only the major version number is checked.
SUPPORTED_AXM_VER = (3, 1)
# Only need to check the version once.
version_checked = False


def get_version(line):
    if not version_checked:
        ver_float = float(line)
        major_ver = math.floor(ver_float)
        if not major_ver == SUPPORTED_AXM_VER[0]:
            msg_handler.error(
                f"Map file is for v{major_ver}. Only v{SUPPORTED_AXM_VER[0]} is supported."
            )


# List of files and sections to ignore
ignore_list = []
# Dictionary of mappings to remove for
# each file and section.
del_dict = {}


def ignore(line):
    global ignore_list
    if not is_sect(line):
        msg_handler.error("Failed AVOID. Expected sect struct in axm file.")
    file_section_tuple = parse_sect(line)
    ignore_list += [file_section_tuple]


def purge_data(line):
    global del_dict
    if line in ax_inputcol_dict[(cur_file, cur_sect)]:
        del_dict[(cur_file, cur_sect)] = line
    elif (cur_file, sect_fallback) in ax_inputcol_dict and line in ax_inputcol_dict[
        (cur_file, sect_fallback)
    ]:
        del_dict[(cur_file, sect_fallback)] = line
    elif (
        file_fallback,
        sect_fallback,
    ) in ax_inputcol_dict and line in ax_inputcol_dict[(file_fallback, sect_fallback)]:
        del_dict[(file_fallback, sect_fallback)] = line
    else:
        msg_handler.error("Failed DEL. Variable to delete does not exist.")


# This deletes the data referred to by purge_data().
# It is in a seperate function because it needs to actually
# be removed after most of finalize() has been run.
# Otherwise, as things are being rearranged, deleted
# variables for certain files and sections will return.
def garbage_collect():
    global ax_inputcol_dict
    for file_section_ax_col in del_dict:
        file_section = file_section_ax_col[0]
        file_name = file_section[0]
        section_name = file_section[1]
        ax_col = file_section_ax_col[1]
        if file_name == file_fallback:
            for file_sect_tuple in ax_inputcol_dict:
                if ax_col in ax_inputcol_dict[file_sect_tuple]:
                    del ax_inputcol_dict[file_sect_tuple][ax_col]
        elif section_name == sect_fallback:
            for file_sect_tuple in ax_inputcol_dict:
                sect_name = file_sect_tuple[1]
                if ax_col in ax_inputcol_dict[file_name, sect_name]:
                    del ax_inputcol_dict[file_name, sect_name][ax_col]
        else:
            del ax_inputcol_dict[file_section][ax_col]


def set_cur_sect(line):
    global cur_file
    global cur_sect
    if not is_sect(line):
        msg_handler.error("Failed SECT. Expected sect struct in axm file.")
    file_section_tuple = parse_sect(line)
    cur_file = file_section_tuple[0]
    cur_sect = file_section_tuple[1]


# Commands can change the target
# file and section (usually common).
# They can modify dictionaries and
# variables, but they never directly
# modify strings.
COMMAND_PREFIX = "!"
COMMANDS = {
    "AXM": get_version,
    "SECT": set_cur_sect,
    "DEL": purge_data,
    "AVOID": ignore,
}
file_fallback = "common"
sect_fallback = "common"
cur_file = file_fallback
cur_sect = sect_fallback
used_files = [file_fallback]
used_sect = [sect_fallback]

# It is neccessary to know exactly where
# command is located in string, as there
# might be nested commands. In that case,
# the first one found will be used.
def find_command(haystack):
    global COMMANDS
    command_order = []
    for needle in COMMANDS:
        if (needle_pos := haystack.find(COMMAND_PREFIX + needle)) > -1:
            command_order += [(needle, needle_pos)]
    incr = 0
    # cur_pos keeps track of the position an
    # operator was found in haystack, while
    # cur_index keeps track of where the former
    # was found in command_order.
    cur_pos = None
    cur_index = None
    for command_pos in command_order:
        cur_order = command_pos[1]
        if cur_index is None:
            cur_index = 0
        if cur_pos is None:
            cur_pos = cur_order
        else:
            if cur_order < cur_pos:
                cur_pos = cur_order
                cur_index = incr
        incr += 1
    return command_order[cur_index][0]


# Removes command from string.
# Doesn't actually ignore the commands
# in the axm file.
def remove_command(string, command):
    command_with_prefix = COMMAND_PREFIX + command
    command_start = string.find(command_with_prefix)
    incr = 0
    if command_start > -1:
        tmp_list = list(string)
        # Use the length of the command portion of
        # string to control how long to delete
        # at a position in order to remove the
        # command text.
        command_len = len(command_with_prefix)
        while incr < command_len:
            del tmp_list[command_start]
            incr += 1
        return "".join(tmp_list).strip()
    return string


# Contains what is included in the
# map file in a form more usable by the
# script. It is keyed by (file, sect).
ax_inputcol_dict = {}


def init(axm_fptr):
    global ax_inputcol_dict
    global COMMANDS
    global cur_file
    global cur_sect
    # Convert the new line char to a space to that it will be removed
    # when the whitespace at the beginning and at the end of the string
    # is stripped.
    line = axm_fptr.readline().replace("\n", " ").lstrip().rstrip()
    if "#" in line:
        line = split_n_strip(line, "#")
        # If the entire line is a comment,
        # split_n_strip() will return an
        # empty string in the first position
        # of the list. Otherwise, the first position
        # will just be the text without the comment.
        line = line[0]
    # Certain mappings can be made optional (non-failing)
    # by adding ~ to the front of the line.
    optional = False
    if "~" in line:
        optional = True
        line = line.removeprefix("~")
    # Guards against blank lines and commented lines.
    if len(line) > 0:
        if COMMAND_PREFIX in line:
            found_command = find_command(line)
            COMMANDS[found_command](remove_command(line, found_command))
        else:
            # Stores the tuples returned by the parser functions.
            parsed_tuple = None
            for oper in oper_types.values():
                if oper[0](line):
                    parsed_tuple = oper[1](line)
                    break
            if parsed_tuple is None:
                msg_handler.error("No valid operator was found.")
            while None in parsed_tuple[1]:
                if not optional:
                    msg_handler.error("Attemped to use axm variable before assignment.")
                parsed_tuple[1].remove(None)
            # Check that (cur_file, cur_sect) is already
            # in ax_inputcol_dict.
            if (cur_file, cur_sect) not in ax_inputcol_dict:
                ax_inputcol_dict[(cur_file, cur_sect)] = {}
            axelor_col_name = parsed_tuple[0]
            input_col_names = parsed_tuple[1]
            # input_col_names would always have at least one entry.
            # Input columns are always uppercase, so if it isn't, that
            # means a greater than symbol was used and input_col_names[0]
            # would be the target axelor column name.
            ax_inputcol_dict[(cur_file, cur_sect)][axelor_col_name] = [
                input_col_names,
                optional,
            ]


# Append all the input_columns from the fallback file and sections
# to where they are supposed to be.
def finalize():
    global ax_inputcol_dict
    # A dictionary to hold the proper values for all files.
    global_dict = {}
    for file_section in ax_inputcol_dict:
        file_name = file_section[0]
        section_name = file_section[1]
        if section_name == sect_fallback:
            global_dict[file_name] = {}
            for ax_input_tuple in ax_inputcol_dict[file_section].items():
                ax_col = ax_input_tuple[0]
                input_cols = ax_input_tuple[1][0]
                is_optional = ax_input_tuple[1][1]
                global_dict[file_name][ax_col] = [input_cols, is_optional]
    for file_section in ax_inputcol_dict:
        file_name = file_section[0]
        # Since the generic file_fallback is more generic, start off
        # with that which is less generic (file-specific).
        if file_name != file_fallback and file_name in global_dict:
            for ax_col in global_dict[file_name]:
                if ax_col not in ax_inputcol_dict[file_section]:
                    ax_inputcol_dict[file_section][ax_col] = global_dict[file_name][
                        ax_col
                    ]
    # Deal with the most generic.
    if file_fallback in global_dict:
        for ax_col in global_dict[file_fallback]:
            for file_section in ax_inputcol_dict:
                file_name = file_section[0]
                if file_name == file_fallback:
                    continue
                if ax_col not in ax_inputcol_dict[file_section]:
                    ax_inputcol_dict[file_section][ax_col] = global_dict[file_fallback][
                        ax_col
                    ]
    # Removes variables that have already
    # been declared to be deleted.
    garbage_collect()


# References to filenames in the axm file
# might not be an absolute value. It could
# simply be just the base filename or a relative path.
def get_file_name(file_name):
    return_name = ""

    # The ignore list should also be checked for appropriate filenames.
    # That way, the appropriate files and sections can later be ignored.
    file_section_list = list(ax_inputcol_dict.keys()) + ignore_list

    for file_section in file_section_list:
        axm_file_name = file_section[0]
        if (
            file_name == axm_file_name
            or os.path.abspath(file_name) == axm_file_name
            or os.path.relpath(file_name) == axm_file_name
            or os.path.basename(file_name) == axm_file_name
        ):
            return_name = axm_file_name
            break
    # The ignore_list should also be checked for
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
def get_sect_name(sect_name):
    return_name = ""

    # The ignore list should also be checked for appropriate section names.
    # That way, the appropriate files and sections can later be ignored.
    file_section_list = list(ax_inputcol_dict.keys()) + ignore_list

    for file_section in file_section_list:
        axm_sect_name = file_section[1]
        if sect_name == axm_sect_name:
            return_name = axm_sect_name
            break
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

    file_section_list = list(ax_inputcol_dict.keys()) + ignore_list
    if file_section not in file_section_list:
        return None
    return file_section


# This function prints messages to the log (and possibly to the screen)
# when an axelor column can't be mapped.
def missing_col_msg(col_list, file_name, section_name, is_optional):
    if len(col_list) > 0:
        msg_func = None
        opt_or_req = ""
        if is_optional:
            msg_func = msg_handler.info
            opt_or_req = "optional"
        else:
            msg_func = msg_handler.error
            opt_or_req = "required"
        msg_str = string.Template(
            "The following $opt_or_req Axelor columns could not be set for $id: "
        ).substitute(
            opt_or_req=opt_or_req, id=msg_handler.get_xlsx_id(file_name, section_name)
        )
        for col in col_list:
            msg_str += col + ", "
        msg_str = msg_str.removesuffix(", ")
        msg_str += "."
        msg_func(msg_str)


def get_axm_data(file_name, section_name, input_columns):
    file_section = get_file_sect(file_name, section_name)
    if file_section is None:
        msg_handler.error(
            string.Template("No mapping exists for $id.").substitute(
                id=msg_handler.get_xlsx_id(file_name, section_name)
            )
        )
    # Not sure why one would want to do this, but it is technically possible for
    # someone to !AVOID an entire file.
    if file_section in ignore_list or (file_section[0], sect_fallback) in ignore_list:
        return None

    file_section_map = {}
    # First, test all possible input columns for exact input_column matches.
    for ax_col in ax_inputcol_dict[file_section]:
        # Default to None.
        file_section_map[ax_col] = None
        possible_input_cols = ax_inputcol_dict[file_section][ax_col][0]
        for possible_col in possible_input_cols:
            for input_col in input_columns:
                if possible_col == input_col.upper():
                    file_section_map[ax_col] = input_col
                    break
        # Then, try to find possible_col within input_col.
        if file_section_map[ax_col] is None:
            for possible_col in possible_input_cols:
                for input_col in input_columns:
                    if possible_col in input_col.upper():
                        file_section_map[ax_col] = input_col
                        break
    # Check for any remaining None variables in file_section_map.
    optional_ax_cols = []
    required_ax_cols = []
    for ax_input_tuple in file_section_map.items():
        found_col = ax_input_tuple[1]
        if found_col is None:
            ax_col = ax_input_tuple[0]
            is_optional = ax_inputcol_dict[file_section][ax_col][1]
            if is_optional:
                optional_ax_cols += [ax_col]
                # Remove so that None won't be in the dictionary
                # the function returns.
                del file_section_map[ax_col]
            else:
                required_ax_cols += [ax_col]
    missing_col_msg(optional_ax_cols, file_name, section_name, True)
    missing_col_msg(required_ax_cols, file_name, section_name, False)
    return file_section_map


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
