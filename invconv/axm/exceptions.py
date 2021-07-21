# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import sys

AXM_ERROR_CODE = 2
AXM_MSG_ID = "(from axm) "


def _fatal_error(error_msg):
    msg_with_id = AXM_MSG_ID + error_msg
    print(msg_with_id, file=sys.stderr)
    sys.exit(AXM_ERROR_CODE)


# Base class
# Aims to allow end users to handle any AXM exception
# with ease.
class axm_exception(Exception):
    pass


class axm_name_exists(axm_exception):
    def __init__(self, name):
        error_msg = f"Name {name} already exists."
        _fatal_error(error_msg)


class axm_invalid_name(axm_exception):
    def __init__(self, name):
        error_msg = f"Name {name} cannot be used, as it is reserved."
        _fatal_error(error_msg)


class axm_invalid_oper_syntax(axm_exception):
    def __init__(self, name):
        error_msg = f"Invalid usage of {name} operator."
        _fatal_error(error_msg)


class axm_invalid_command_syntax(axm_exception):
    def __init__(self, name):
        error_msg = f"Invalid usage of {name} command."
        _fatal_error(error_msg)


class axm_command_not_recognized(axm_exception):
    def __init__(self, command):
        error_msg = f"{command} is not recognized."
        _fatal_error(error_msg)


class axm_invalid_ver(axm_exception):
    def __init__(self, ver, expected_ver):
        error_msg = f"Version {ver} is not compatible with {expected_ver}."
        _fatal_error(error_msg)


class axm_mean_val(axm_exception):
    def __init__(self, val):
        error_msg = (
            f"The nice value {val} is invalid. No negatives allowed for scheduler."
        )
        _fatal_error(error_msg)


class axm_operator_no_effect(axm_exception):
    def __init__(self, name):
        error_msg = f"The operator {name} has no effect."
        _fatal_error(error_msg)


class axm_operator_not_found(axm_exception):
    def __init__(self, line):
        error_msg = f'No operator was found in line: "{line}".'
        _fatal_error(error_msg)


class axm_unexpected_command(axm_exception):
    def __init__(self, name):
        error_msg = f"The command {name} was unexpectedly used."
        _fatal_error(error_msg)


class axm_invalid_file_section(axm_exception):
    def __init__(self, file_name, section_name):
        error_msg = f"The file section pair ({file_name}, {section_name}) cannot be found in axm file."
        _fatal_error(error_msg)


class axm_expected_var_not_found(axm_exception):
    def __init__(self, var, filename, sectionname):
        error_msg = f"The variable {var} could not be resolved from FILE: {filename}, SECTION: {sectionname}."
        _fatal_error(error_msg)


class axm_source_not_iterable(axm_exception):
    def __init__(self, object_):
        error_msg = f"Object must be iterable: {str(object_)}"
        _fatal_error(error_msg)
