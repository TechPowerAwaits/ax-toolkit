# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import collections
import string

from loguru import logger

try:
    from exceptions import InvconvInvalidFileType
except ModuleNotFoundError:
    from invconv.exceptions import InvconvInvalidFileType

# This dict holds functions that
# deal with a specific file type.
_input_types = {}
_default_input_type = None

# This function adds new file types
# to the list.
def add(type_, func):
    global _input_types
    # Append type_ with underscore
    # and number if it is already
    # in dict. It starts at 0.
    incr = 0
    new_type = type_
    while new_type in _input_types:
        final_pos = len(new_type) - 1
        count = 0
        tmp_type_deque = collections.deque()
        tmp_type_deque.extend(new_type)
        if "_" in new_type and new_type[final_pos] in string.digits:
            if count == 0:
                # If an underscore and digit is in type_
                # originally passed to function, raise
                # exception.
                raise InvconvInvalidFileType(type_)
            tmp_type_list = new_type.split("_")
            num_str = tmp_type_list[-1]
            try:
                incr = int(num_str)
            except (TypeError, ValueError):
                raise InvconvInvalidFileType(type_)
            # Remove the underscore and other values
            # from deque.
            underscore_pos = new_type.rfind("_")
            index = underscore_pos
            while index <= final_pos:
                del tmp_type_deque[underscore_pos]
                index += 1
        tmp_type_deque.append("_" + int(incr))
        new_type = "".join(tmp_type_deque)
        incr += 1
    # Create a warning in log if number has been appended to type_.
    if incr > 0:
        logger.warning(f'Filetype "{type_}" already exists. Changing to "{new_type}".')
    # If the above warning is printed, it is already
    # obvious that the type has been loaded.
    logger.info(f'Type "{type_}" has been loaded.')
    # Before changing _input_types, check if it is empty,
    # and if so, set the default value to new_type.
    if not _input_types:
        set_default(new_type)
    _input_types[new_type] = func


def list_types():
    return list(_input_types.keys())


def get_func(type_=None):
    if type_ is None:
        # Return list of every function.
        return list(_input_types.values())
    return _input_types[type_]


# By default, the default ftype
# is the first file type added
# to dict. Can be overriden.
def set_default(type_):
    global _default_input_type
    _default_input_type = type_


def get_default():
    return _default_input_type


# Common classes across modules defining
# new types.

# All of the ftype functions are expected to return a list
# containing elements of this class. Allows easy access
# to headers (a list). Developers are expected to subclass
# it to add a parser function that keeps track of what it
# parsed last and returns str values. Once there is nothing
# else to parse, it will return None and then parse from the
# beginning.
class BasicFtypeDataClass:
    def __init__(self, filename, sectionname, headers):
        self.filename = filename
        self.sectionname = sectionname
        self.headers = headers

    # __str__ is designed to render it similar
    # to a tuple.
    def __str__(self):
        return f"('{self.filename}', '{self.sectionname}', {str(self.headers)})"

    # Have __repr__ render the same as __str__.
    __repr__ = lambda self: self.__str__()

    def __eq__(self, obj):
        # Check if an attribute in obj
        # matches filename and sectionname.
        found_filename = False
        found_sectionname = False
        for attr in dir(obj):
            if self.filename == getattr(obj, attr):
                found_filename = True
            if self.sectionname == getattr(obj, attr):
                found_sectionname = True
        if found_filename and found_sectionname:
            return True
        # If obj is iterable, check it for the proper
        # values in a certain order.
        if hasattr(obj, "__iter__"):
            if len(obj) == 2:
                if obj[0] == self.filename and obj[1] == self.sectionname:
                    return True
            if len(obj) == 3:
                if (
                    obj[0] == self.filename
                    and obj[1] == self.sectionname
                    and obj[2] == self.headers
                ):
                    return True
        return False

    def __iter__(self):
        self._cur_pos = 0
        return self

    def __next__(self):
        return_val = None
        if self._cur_pos == 0:
            return_val = self.filename
        elif self._cur_pos == 1:
            return_val = self.sectionname
        elif self._cur_pos == 2:
            return_val = self.headers
        else:
            raise StopIteration
        self._cur_pos += 1
        return return_val

    def __len__(self):
        return_num = 0
        # Run __iter__() to reset
        # cur_pos count.
        self.__iter__()
        while True:
            try:
                self.__next__()
                return_num += 1
            except StopIteration:
                break
        return return_num


# All ftype functions are expected to use this list
# as it contains convenience functions that
# are used by the rest of the script.
class FtypeDataList(collections.UserList):
    def __init__(self, list_=None):
        # Keep track of index for parser func.
        self.cur_index = None
        self._list = list_
        super().__init__(self._list)

    def __dict__(self):
        return_dict = {}
        # Ensure list contains class or subclass of
        # BasicFtypeDataClass.
        for item in self.data:
            if not isinstance(item, BasicFtypeDataClass):
                return None
            return_dict[(item.filename, item.sectionname)] = item.headers
        return return_dict

    # Alias for __dict__().
    headers = lambda self: self.__dict__()

    def parser(self):
        # Ensure list contains elements that have parser
        # method. Only need to check once. Since the function
        # will be run multiple times, checking every time will
        # probably slow it down.
        if not hasattr(self, "_parser_valid"):
            self._parser_valid = True
            for item in self.data:
                if not hasattr(item, "parser") or not callable(getattr(item, "parser")):
                    self._parser_valid = False
                    break
        if not self._parser_valid:
            return None

        if self.cur_index is None:
            self.cur_index = 0
        item_parser_result = self.data[self.cur_index].parser()
        item_filename = self.data[self.cur_index].filename
        item_sectionname = self.data[self.cur_index].sectionname
        item_headers = self.data[self.cur_index].headers
        # If item_parser_result is None,
        # it has probably parsed everything
        # from the element in the list.
        if item_parser_result is not None:
            return (item_filename, item_sectionname, item_headers, item_parser_result)
        self.cur_index += 1
        final_pos = len(self.data) - 1
        # Return None if no elements are
        # remaining.
        if self.cur_index > final_pos:
            self.cur_index = None
            return None
        # Rerun parser to get value.
        return self.parser()
