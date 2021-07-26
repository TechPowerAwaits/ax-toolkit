# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import axm.common
import axm.command
from axm.exceptions import AxmOperatorNotFound
import axm.operator
import axm.scheduler
import axm.utils

# Copies a list of input columns for later processing.
def init(input_col):
    axm.common.input_col_dict = input_col


def parse(axm_fptr):
    # Convert the new line char to a space to that it will be removed
    # when the whitespace at the beginning and at the end of the string
    # is stripped.
    line = axm_fptr.readline().replace("\n", " ").strip()
    if "#" in line:
        line = axm.utils.split_n_strip(line, "#")
        # If the entire line is a comment,
        # split_n_strip() will return an
        # empty string in the first position
        # of the list. Otherwise, the first position
        # will just be the text without the comment.
        line = line[0]
    # Guards against blank lines and commented lines.
    if len(line) > 0:
        if axm.command.verify(line):
            for command_type in axm.command.get(axm.command.ALL_COMMANDS):
                if command_type.check_func(line):
                    # All action functions for every
                    # command must remove the command prefix
                    # itself. For example, "!AXM 3.0" will
                    # be passed as such to action_func.
                    # It won't be stripped down to "3.0".
                    command_type.action_func(line)
        else:
            # The reason a for loop isn't used is so all operators
            # can be looked at again. An operator should be expected
            # to be found at least once, as commands are already dealt
            # with and blank/commented lines are ignored, making
            # operators the only logical choice for existance in a
            # line.
            is_oper_found = False
            oper_list = axm.operator.get(axm.operator.ALL_OPERATORS)
            index = 0
            oper_max_pos = len(oper_list) - 1
            while index <= oper_max_pos:
                oper = oper_list[index]
                index += 1
                if oper.find_func(line) > -1:
                    is_oper_found = True
                    # Action functions only return values
                    # to overwrite the currently used line.
                    return_val = oper.action_func(line)
                    if return_val is not None:
                        line = return_val
                        # Reset incr so that all operators
                        # are looked at again.
                        index = 0
            if not is_oper_found:
                raise AxmOperatorNotFound(line)


# Processes all the things that need to be processed.
def finalize():
    func_deque = axm.scheduler.get(axm.scheduler.ALL_SCHEDULED)
    func_deque_len = len(func_deque)
    incr = 0
    while incr < func_deque_len:
        func_deque.popleft().run()
        incr += 1
