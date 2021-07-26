# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import string
import types

import axm.common
from axm.exceptions import AxmInvalidName, AxmNameExists, AxmOperatorNoEffect
import axm.scheduler
import axm.utils


class oper_tuple:
    def _default_action_func(self, line, parse_func):
        parse_result = parse_func(line)
        if (axm.common.cur_file, axm.common.cur_sect) not in axm.common.out_input_col:
            axm.common.out_input_col[(axm.common.cur_file, axm.common.cur_sect)] = {}
        axm.common.out_input_col[(axm.common.cur_file, axm.common.cur_sect)][
            parse_result[0]
        ] = parse_result[1]

    def _default_find_func(self, line):
        symbol = self.symbol
        return_val = -1
        if symbol in line:
            symbol_len = len(symbol)
            symbol_start = line.find(symbol)
            if symbol_len == 0:
                # Likely would be a mistake.
                return_val = -1
            # Some operators use quotes.
            elif '"' in line:
                # If an operator is beyond a quotation
                # mark, then likely it wasn't meant
                # to be an operator and is just part
                # of a string.
                if line.find('"') > symbol_start:
                    return_val = symbol_start
                else:
                    return_val = -1
            elif symbol_len == 1:
                # Need to confirm operator is by itself.
                if is_single(line, symbol_start):
                    return_val = symbol_start
            else:
                # Ensure that this longer operator
                # is not just part of an even larger operator.
                symbol_end = symbol_start + symbol_len
                after_symbol = symbol_end + 1
                if not line[after_symbol] in string.punctuation:
                    return_val = symbol_start
        return return_val

    def _default_parse_func(self, line):
        symbol = self.symbol
        return_tuple = (None, None)
        if self.find_func(line):
            ax_input_map = axm.utils.split_n_strip(line, symbol)
            axelor_col_name = ax_input_map[0]
            input_col_names = axm.utils.split_n_strip(ax_input_map[1], ",")
            return_tuple = (axelor_col_name, input_col_names)
        return return_tuple

    def _catch_invalid(self, val, fallback):
        # Ensures that no values passed during creation of instances of
        # the class are invalid.
        return_val = None
        if isinstance(val, types.FunctionType):
            return_val = val
        else:
            return_val = fallback
        return return_val

    def __init__(
        self,
        symbol,
        find_func=_default_find_func,
        parse_func=_default_parse_func,
        base_action_func=_default_action_func,
    ):
        default_find_func = self._default_find_func
        default_parse_func = self._default_parse_func
        default_action_func = self._default_action_func
        self.symbol = symbol
        self.find_func = self._catch_invalid(find_func, default_find_func)
        self.parse_func = self._catch_invalid(parse_func, default_parse_func)
        self.base_action_func = self._catch_invalid(
            base_action_func, default_action_func
        )

    # The action_func will pass the proper
    # parse_func to base_action_func.
    def action_func(self, line):
        parse_func = self.parse_func
        return self.base_action_func(line, parse_func)


# This dictionary contains all valid operators.
# New operators can easily be added.
_oper_dict = {}
ALL_OPERATORS = "*"


def add(name, symbol, find_func=None, parse_func=None, action_func=None):
    global _oper_dict
    if name == ALL_OPERATORS:
        raise AxmInvalidName
    if name in _oper_dict:
        raise AxmNameExists
    _oper_dict[name] = oper_tuple(symbol, find_func, parse_func, action_func)


def get(name):
    if name == ALL_OPERATORS:
        return list(_oper_dict.values())
    if name in _oper_dict:
        return _oper_dict[name]
    return None


# Could find if a name exists, but
# finding if a symbol already exists is more
# accurate.
def symbol_exists(symbol):
    for name_tuple in _oper_dict.items():
        if symbol == name_tuple[1].symbol:
            return True
    return False


# Returns True if only one character is used
# as an operator. False otherwise.
def is_single(line, oper_loc):
    pre_oper_loc = oper_loc - 1
    post_oper_loc = oper_loc + 1

    if not (
        line[pre_oper_loc] in string.punctuation
        and line[post_oper_loc] in string.punctuation
    ):
        return True
    return False


# Return the first operator in a given string.
def lfind(line):
    first_pos = None
    first_name = None
    for oper_name in _oper_dict:
        oper_pos = _oper_dict[oper_name].find_func(line)
        if oper_pos > -1:
            if first_pos is None:
                first_pos = oper_pos
            if first_name is None:
                first_name = oper_name
            if oper_pos > first_pos:
                first_pos = oper_pos
                first_name = oper_name
    if first_name is not None:
        return _oper_dict[first_name]
    return None


###    The basic operators available with axm and supporting functions.    ###

_OPT_SYMBOL = "~"


def _find_opt(line):
    # Optional operator needs to be first thing
    # on the line (excluding whitespace).
    test_string = line.lstrip()
    if test_string.find(_OPT_SYMBOL) == 0:
        return 0
    return -1


def _parse_opt(line):
    if _find_opt(line) > -1:
        return line.lstrip().removeprefix(_OPT_SYMBOL)
    return line


def _act_opt(line, parse_func):
    parsed_str = parse_func(line)
    output_col = ""
    # Search for other operators.
    # Function assumes the other operators
    # use _default_parse_function.
    # No other parser is currently supported.
    # Result ends up in output_col.
    search_for_opers = True
    while search_for_opers:
        tuple_or_none = lfind(parsed_str)
        if tuple_or_none is not None:
            output_col = tuple_or_none.parse_func(parsed_str)[0]
            # Operator has been found and output_col is now presumably by
            # itself (without any operators present). Therefore, the
            # search for operators is at an end.
            search_for_opers = False
    if (axm.common.cur_file, axm.common.cur_sect) not in axm.common.opt_dict:
        axm.common.opt_dict[(axm.common.cur_file, axm.common.cur_sect)] = []
    axm.common.opt_dict[(axm.common.cur_file, axm.common.cur_sect)].append(output_col)
    # Returns the initially parsed string (removed the opt symbol)
    # so that it can replace the string used for other operations
    # in a parser function.
    return parsed_str


if not symbol_exists(_OPT_SYMBOL):
    add(
        "opt",
        _OPT_SYMBOL,
        find_func=_find_opt,
        parse_func=_parse_opt,
        action_func=_act_opt,
    )
    axm.scheduler.add(
        axm.common.specialize, axm.scheduler.NICE_INHERIT, [axm.common.opt_dict]
    )
    axm.scheduler.add(
        axm.common.inherit, axm.scheduler.NICE_INHERIT, [axm.common.opt_dict]
    )


_ASSIGN_SYMBOL = ":"
if not symbol_exists(_ASSIGN_SYMBOL):
    add("assign", _ASSIGN_SYMBOL)

_DELEGATOR_SYMBOL = ">"
# If the importer operator is used on the
# variable you are delegating to, the
# user-defined string from
# axm.common.column_output_dict needs to
# be copied to the other variable.
def _act_delegator(line, parse_func):
    parsed_str = parse_func(line)
    target_var = parsed_str[0]
    # Multiple delegator vars can be specified at once.
    # In that case, the possible input variables from all
    # of them will be copied over, but only the first valid
    # string in axm.common.column_output_dict will be.
    delegate_vars = parsed_str[1]
    # Need to confirm that something has been copied over. Otherwise,
    # it will raise an exception.
    is_valid_oper = False
    # Need a list to hold all the possible input columns from everywhere else.
    possible_input_cols = []
    for delegate_var in delegate_vars:
        if (axm.common.cur_file, axm.common.cur_sect) in axm.common.out_input_col:
            if (
                delegate_var
                in axm.common.out_input_col[(axm.common.cur_file, axm.common.cur_sect)]
            ):
                possible_input_cols.extend(
                    axm.common.out_input_col[
                        (axm.common.cur_file, axm.common.cur_sect)
                    ][delegate_var]
                )
        if (axm.common.cur_file, axm.common.cur_sect) in axm.common.column_output_dict:
            if (
                target_var
                not in axm.common.column_output_dict[
                    (axm.common.cur_file, axm.common.cur_sect)
                ]
                and delegate_var
                in axm.common.column_output_dict[
                    (axm.common.cur_file, axm.common.cur_sect)
                ]
            ):
                axm.common.column_output_dict[
                    (axm.common.cur_file, axm.common.cur_sect)
                ][target_var] = axm.common.column_output_dict[
                    (axm.common.cur_file, axm.common.cur_sect)
                ][
                    delegate_var
                ]
                is_valid_oper = True
    if len(possible_input_cols) > 0:
        axm.common.out_input_col[(axm.common.cur_file, axm.common.cur_sect)][
            target_var
        ] = possible_input_cols
        is_valid_oper = True
    if not is_valid_oper:
        raise AxmOperatorNoEffect(f"delegator ({_DELEGATOR_SYMBOL})")


if not symbol_exists(_DELEGATOR_SYMBOL):
    add("delegator", _DELEGATOR_SYMBOL, action_func=_act_delegator)

_IMPORTER_SYMBOL = "<"


def _parse_importer(line):
    axcol_string = axm.utils.split_n_strip(line, _IMPORTER_SYMBOL)
    axcol_name = axcol_string[0]
    user_given_string = axcol_string[1].removeprefix('"').removesuffix('"')
    return (axcol_name, user_given_string)


def _act_importer(line, parse_func):
    parsed_val = parse_func(line)
    axcol_name = parsed_val[0]
    user_str = parsed_val[1]
    if (axm.common.cur_file, axm.common.cur_sect) not in axm.common.column_output_dict:
        axm.common.column_output_dict[(axm.common.cur_file, axm.common.cur_sect)] = {}
    axm.common.column_output_dict[(axm.common.cur_file, axm.common.cur_sect)][
        axcol_name
    ] = user_str
    # If the user_str doesn't contain a variable depending on input,
    # add to axm.common.opt_list to prevent the script from complaining
    # that a valid input column wasn't found.
    if not (
        axm.common.INPUT_COL_VAR in user_str and axm.common.INPUT_TXT_VAR in user_str
    ):
        if (axm.common.cur_file, axm.common.cur_sect) not in axm.common.opt_dict:
            axm.common.opt_dict[(axm.common.cur_file, axm.common.cur_sect)] = []
        axm.common.opt_dict[(axm.common.cur_file, axm.common.cur_sect)].append(
            axcol_name
        )


if not symbol_exists(_IMPORTER_SYMBOL):
    add(
        "importer",
        _IMPORTER_SYMBOL,
        parse_func=_parse_importer,
        action_func=_act_importer,
    )


axm.scheduler.add(
    axm.common.specialize, axm.scheduler.NICE_INHERIT, [axm.common.out_input_col]
)
axm.scheduler.add(
    axm.common.inherit, axm.scheduler.NICE_INHERIT, [axm.common.out_input_col]
)
