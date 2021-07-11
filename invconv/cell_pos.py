# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import math
import string

# Similar to range(),
# except it starts at 1 and
# includes col_len.
def col_iter(*col_args):
    col_len = 0
    col_start = 0
    iter_list = []

    if len(col_args) == 1:
        col_start = 1
        col_len = col_args[0]
    else:
        col_start = col_args[0]
        col_len = col_args[1]

    if col_len > 1:
        cur_val = col_start
        while cur_val <= col_len:
            iter_list.append(cur_val)
            cur_val += 1
    else:
        iter_list = None
    return iter_list


# Note:  This version of the get_col_letter() function returns
#        the correct Excel-equivalent column labels from "A" to
#        "AYY" when provided with corresponding parameter values
#        ranging from 1 to 1,352.  However, with a parameter
#        value of 1,353 this function generates incorrect output.
#
# Author: Daryl Johnston
# SPDX-license-identifier: Zlib
#
# "col_num" must start at 1.
def get_col_letter(col_num):
    NUM_UPPERCASE_LETTERS = 26
    col_letters = ""

    # Determine the number of letters required to represent
    # this value.
    #
    # Note:  The "col_num" value should always be greater
    #        than zero.  If it isn't greater than zero then
    #        we can't use a log() function to determine the
    #        number of letters, so assume at least one
    #        letter is going to be required.
    num_letters = 1
    if col_num > 0:
        num_letters = math.floor(math.log(col_num, NUM_UPPERCASE_LETTERS))

        # At this point the "num_letters" value may or may not
        # need to be incremented by one.  First we need to check
        # whether a "max_value" representation consisting only
        # of this many 'Z' characters would still be large enough
        # to hold this "col_num" value.
        #
        # Note:  Based on our previous assumption that at least
        #        one letter ('Z') will be required, the "max_value"
        #        will at least be "NUM_UPPERCASE_LETTERS").
        max_value = NUM_UPPERCASE_LETTERS
        for n in range(2, num_letters + 1):
            max_value += math.pow(NUM_UPPERCASE_LETTERS, n)
        if num_letters == 0 or col_num > max_value:
            num_letters += 1

    # Replaced string append with string join. DJ20210715
    #
    # Create an empty list of strings.
    listOfStrings = []

    # Determine the combination of letters required
    # to represent the specified "col_num" value.
    #
    # Note:  For improved efficiency the "col_num"
    #        value is reused here to calculate
    #        intermediate values.
    for letter_idx in range(num_letters, 0, -1):
        letter_index = math.floor(
            col_num / math.pow(NUM_UPPERCASE_LETTERS, letter_idx - 1)
        )

        # At this point the "letter_index" value may
        # or may not need to be decremented by one.
        #
        # If this column is greater than (i.e. to the
        # left of) the ones column then we need to
        # check the current representation.
        # Specifically, we need to compare the current
        # "col_num" value with a fictitious value
        # consisting of the current "letter_index"
        # followed only by non-existent zero values.
        # If that fictitious value could still
        # represent the "col_num" value then we know
        # the next smaller lead "letter_index" could
        # also be used to represent the same value,
        # since zero values are not supported.
        if letter_idx > 1:
            if col_num <= letter_index * math.pow(
                NUM_UPPERCASE_LETTERS, letter_idx - 1
            ):
                letter_index -= 1

        # Replaced string append with string join. DJ20210715
        listOfStrings.append(string.ascii_uppercase[letter_index - 1])

        col_num -= letter_index * int(math.pow(NUM_UPPERCASE_LETTERS, letter_idx - 1))

    col_letters = "".join(listOfStrings)
    return col_letters


def row_iter(*row_args):
    # Since row_iter and col_iter
    # are mostly the same, use one
    # definition.
    if len(row_args) == 1:
        return col_iter(row_args[0])
    if len(row_args) > 1:
        return col_iter(row_args[0], row_args[1])
    return None
