# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

# Everything scheduled runs as part of axm.parser.finalize() function.

import collections

try:
    from axm.exceptions import AxmMeanValError
except ModuleNotFoundError:
    from invconv.axm.exceptions import AxmMeanValError

# Constants.
NICE_INHERIT = 0
NICE_DEL_N_AVOID = 1
NICE_VALID_COL = 25
NICE_OUT_STRING = 30


class _scheduler_internal_def:
    def _get_func_name(self):
        func_str = str(self.func)
        func_str = func_str.removeprefix("<function ")
        whitespace_loc = func_str.find(" ")
        incr = whitespace_loc
        max_func_pos = len(func_str) - 1
        # A list is more flexible for deleting
        # stuff off of than a string.
        func_list = list(func_str)
        while incr <= max_func_pos:
            del func_list[whitespace_loc]
            incr += 1
        func_name = "".join(func_list)
        return func_name

    def __init__(self, func, nice, param_list=None):
        self.func = func
        self.func_name = self._get_func_name()
        if param_list is None:
            self.param_list = []
        else:
            self.param_list = param_list
        if nice < 0:
            raise AxmMeanValError(nice)
        self.nice = nice

    def convert(self):
        if isinstance(self.param_list, dict):
            return _scheduler_dict_def(self.func, self.param_list)
        return _scheduler_list_def(self.func, self.param_list)


class _scheduler_common_def:
    def __init__(self, func, param_list):
        self.func = func
        self.param_list = param_list


class _scheduler_list_def(_scheduler_common_def):
    def run(self):
        func = self.func
        param_list = self.param_list
        func(*param_list)


class _scheduler_dict_def(_scheduler_common_def):
    def run(self):
        func = self.func
        param_dict = self.param_list
        func(**param_dict)


# This contains all the functions needed to manage schedulers of the parsed data.

_scheduler_list = []
ALL_SCHEDULED = "*"
# This corresponds with the smallest nice value possible.
# It doesn't neccesarily mean that the value is being used.
MIN_NICE_VAL = 0


def add(func, nice, param_list=None):
    global _scheduler_list
    _scheduler_list.append(_scheduler_internal_def(func, nice, param_list))


# Removes the first definition that had a given nice value.
def remove_first(nice):
    global _scheduler_list
    for index_definition in enumerate(_scheduler_list):
        index = index_definition[0]
        definition = index_definition[1]
        if definition.nice == nice:
            del _scheduler_list[index]
            break


# Removes the last definition added that had a given nice value.
def remove_last(nice):
    global _scheduler_list
    rev_scheduler_list = _scheduler_list.reverse()
    for index_definition in enumerate(rev_scheduler_list):
        rev_index = index_definition[0]
        definition = index_definition[1]
        if definition.nice == nice:
            max_list_pos = len(_scheduler_list) - 1
            index = max_list_pos - rev_index
            del _scheduler_list[index]
            break


# Returns the number of function definitions that are within
# a certain niceness.
def count(nice):
    count_val = 0
    for definition in _scheduler_list:
        if definition.nice == nice:
            count_val += 1
    return count_val


# Removes all the function definitions associated with a given niceness.
def purge(nice):
    while count(nice) > 0:
        remove_first(nice)


# Checks if a function with a given name exists.
def is_func(func_name):
    for definition in _scheduler_list:
        if definition.func_name == func_name:
            return True
    return False


# Removes a definition that has a function with a given name.
def purge_func(func_name):
    global _scheduler_list
    for index_definition in enumerate(_scheduler_list):
        index = index_definition[0]
        definition = index_definition[1]
        if definition.func_name == func_name:
            del _scheduler_list[index]


# Changes all instances of one nice value to another.
# If the destination nice value already exists, it
# is all rearranged so that the recently redesignated
# definitions end up last in that section of the list.
def move(initial_nice, final_nice):
    if count(final_nice) == 0:
        for index_definition in enumerate(_scheduler_list):
            index = index_definition[0]
            definition = index_definition[1]
            if definition.nice == initial_nice:
                _scheduler_list[index].nice = final_nice
    else:
        initial_nice_poslist = []
        final_nice_poslist = []
        for index_definition in enumerate(_scheduler_list):
            index = index_definition[0]
            definition = index_definition[1]
            if definition.nice == initial_nice:
                initial_nice_poslist.append(index)
            elif definition.nice == final_nice:
                final_nice_poslist.append(index)
            else:
                pass
        # Store the definitions in the proper order
        # and add it back to _scheduler_list.
        tmp_def_list = []
        for index in final_nice_poslist:
            tmp_def_list.append(_scheduler_list[index])
        for index in initial_nice_poslist:
            tmp_def = _scheduler_list[index]
            tmp_def.nice = final_nice
            tmp_def_list.append(tmp_def)
        # Remove the current nice values, as
        # all that is required is contained in
        # tmp_def_list.
        purge(initial_nice)
        purge(final_nice)
        for definition in tmp_def_list:
            _scheduler_list.append(definition)


def lowest_nice_val():
    incr = 0
    low_nice_val = None
    while low_nice_val is None:
        nice_count = count(incr)
        if nice_count > 0:
            low_nice_val = incr
    return low_nice_val


def highest_nice_val():
    max_nice_val = None
    for definition in _scheduler_list:
        nice_val = definition.nice
        if max_nice_val is None:
            max_nice_val = nice_val
        else:
            if nice_val > max_nice_val:
                max_nice_val = nice_val
    return max_nice_val


# Creates a deque that contains all the functions in its proper order.
# A deque is used just because it is more optimized in poping values off.
def get(nice):
    return_deque = collections.deque()
    if nice == ALL_SCHEDULED:
        low_nice_val = lowest_nice_val()
        high_nice_val = highest_nice_val()
        if low_nice_val is None or high_nice_val is None:
            return None
        # Lowest nice value has higher priority.
        incr = low_nice_val
        while incr <= high_nice_val:
            nice_deque = get(incr)
            # The nice values between
            # the highest and lowest nice values
            # might not all be used.
            if nice_deque is not None:
                return_deque.extend(nice_deque)
            incr += 1
    else:
        if count(nice) == 0:
            return None
        for definition in _scheduler_list:
            if definition.nice == nice:
                return_deque.append(definition.convert())
    return return_deque
