# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

# Base class
# Aims to allow end users to handle any AXM exception
# with ease.
class AxmException(Exception):
    pass


class AxmNameExists(AxmException):
    def __init__(self, name):
        self.error_msg = f"Name {name} already exists"
        super().__init__(self.error_msg)


class AxmInvalidName(AxmException):
    def __init__(self, name):
        self.error_msg = f"Name {name} cannot be used, as it is reserved"
        super().__init__(self.error_msg)


class AxmInvalidSyntax(AxmException):
    def __init__(self, name, type_):
        self.error_msg = f"Invalid usage of {name} {type_}"
        super().__init__(self.error_msg)


class AxmCommandNotRecognized(AxmException):
    def __init__(self, command):
        self.error_msg = f"{command} is not recognized"
        super().__init__(self.error_msg)


class AxmInvalidVer(AxmException):
    def __init__(self, ver, expected_ver):
        self.error_msg = f"Version {ver} is not compatible with {expected_ver}"
        super().__init__(self.error_msg)


class AxmMeanValError(AxmException):
    def __init__(self, val):
        self.error_msg = f"The nice value {val} is invalid, as no negatives are allowed for scheduler"
        super().__init__(self.error_msg)


class AxmOperatorNoEffect(AxmException):
    def __init__(self, name):
        self.error_msg = f"The operator {name} has no effect"
        super().__init__(self.error_msg)


class AxmOperatorNotFound(AxmException):
    def __init__(self, line):
        self.error_msg = f'No operator was found in "{line}"'
        super().__init__(self.error_msg)


class AxmUnexpectedCommand(AxmException):
    def __init__(self, name):
        self.error_msg = f"The command {name} was unexpectedly used"
        super().__init__(self.error_msg)


class AxmInvalidFileSection(AxmException):
    def __init__(self, file_name, section_name):
        self.error_msg = f"The file section pair ({file_name}, {section_name}) cannot be found in axm file"
        super().__init__(self.error_msg)


class AxmExpectedVarNotFound(AxmException):
    def __init__(self, missing_var_dict):
        tmp_error_list = []
        tmp_error_list.append("The variables ")
        file_section_num = len(missing_var_dict.keys())
        one_var = False
        for fs_index, file_section in enumerate(list(missing_var_dict.keys()), 1):
            if file_section_num == 1 and len(missing_var_dict) == 1:
                one_var = True
                # In case there is only one section with one missing variable,
                # the starting message needs to be reworded.
                tmp_error_list.clear()
                tmp_error_list.append("The variable ")
            file_name = file_section[0]
            section_name = file_section[1]
            tmp_val_list = []
            missing_val_num = len(missing_var_dict[file_section])

            for index, missing_val in enumerate(missing_var_dict[file_section], 1):
                tmp_val_list.append('"')
                tmp_val_list.append(missing_val)
                tmp_val_list.append('"')
                if index == missing_val_num:
                    tmp_error_list.extend(tmp_val_list)
                else:
                    tmp_val_list.append(", ")

            tmp_error_list.append(f" in ({file_name}, {section_name})")
            if fs_index == file_section_num:
                if one_var:
                    # Ending message needs to be reworded.
                    tmp_error_list.append(" is missing")
                else:
                    tmp_error_list.append(" are all missing")

        self.error_msg = "".join(tmp_error_list)
        super().__init__(self.error_msg)


class AxmSourceNotIterable(AxmException):
    def __init__(self, object_):
        # Try to get string form of object; otherwise, fallback
        # to <Unknown> string.
        obj_str = "<Unknown>"
        try:
            obj_str = str(object_)
        except (TypeError, ValueError):
            pass
        self.error_msg = f"Object {obj_str} must be iterable"
        super().__init__(self.error_msg)
