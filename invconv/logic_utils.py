# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

"""Contains utilities used by logic functions."""

import string

# Generic function to check for shorthand
# forms of names in order to reduce the
# number of false positives.
def find_shorthand(haystack, needle):
    haystack_len = len(haystack)
    haystack_final_pos = haystack_len - 1
    needle_len = len(needle)
    needle_final_pos = needle_len - 1

    # Check for exact matches.
    if haystack == needle:
        return True

    # Check if needle is at end of haystack
    # or before a period (ruling out false
    # positives).
    needle_pos = haystack.rfind(needle)
    needle_end = needle_pos + needle_final_pos
    if (
        (
            needle_end == haystack_final_pos
            or (needle_end == (haystack_final_pos - 1) and haystack.endswith("."))
        )
        and (needle_pos - 1) > -1
        and haystack[needle_pos - 1] in string.whitespace
    ):
        return True

    # Check if needle is at beginning of haystack
    # but seperated by a space (ruling out false
    # positives).
    needle_pos = haystack.find(needle)
    needle_end = needle_pos + needle_final_pos
    if (
        needle_pos == 0
        and (needle_end + 1) <= haystack_final_pos
        and haystack[needle_end + 1] in string.whitespace
    ):
        return True

    # Check if needle is seperated by whitespace
    # on either side (ruling out false positives).
    stripped_haystack = haystack
    while (needle_pos := stripped_haystack.find(needle)) > -1:
        needle_end = needle_pos + needle_final_pos
        stripped_haystack_len = len(stripped_haystack)
        stripped_haystack_final_pos = stripped_haystack_len - 1
        # Needs room for a space on the right.
        max_pos = stripped_haystack_final_pos - 1
        # needle_pos cannot be in first position.
        # Else, there will be no room for space
        # before needle_pos. Likewise, needle_end
        # can't be at the end of stripped_haystack.
        # Else, it can't have a space to its right.
        if (
            needle_pos > 0
            and needle_end <= max_pos
            and haystack[needle_pos - 1] in string.whitespace
            and haystack[needle_end + 1] in string.whitespace
        ):
            return True
        # Remove False positive from haystack.
        haystack_list = list(stripped_haystack)
        incr = 0
        while incr <= needle_end:
            del haystack_list[0]
            incr += 1
        stripped_haystack = "".join(haystack_list)

    return False


# A seperate function is required for units,
# as some abbreviated forms can be one character long.
# Need to ensure it is shortly after a number.
def find_unit_shorthand(haystack, needle):
    haystack_len = len(haystack)
    haystack_final_pos = haystack_len - 1
    needle_len = len(needle)
    needle_final_pos = needle_len - 1

    # Check for exact matches.
    if haystack == needle:
        return True

    # Check if unit is at end of haystack (or
    # before a period) and has a digit right
    # before it or whitespace before a digit
    # (ruling out false positives).
    needle_pos = haystack.rfind(needle)
    needle_end = needle_pos + needle_final_pos
    if needle_end == haystack_final_pos or (
        needle_end == (haystack_final_pos - 1) and haystack.endswith(".")
    ):
        # Ensure needle_pos has enough room for a
        # digit before it.
        if (needle_pos - 1) > -1 and haystack[needle_pos - 1] in string.digits:
            return True
        # Ensure needle_pos has enough room for a
        # digit and whitespace before it.
        if (
            (needle_pos - 2) > -1
            and haystack[needle_pos - 1] in string.whitespace
            and haystack[needle_pos - 2] in string.digits
        ):
            return True

    # Check if unit is surrounded by spaces
    # or is next to a digit and seperated
    # from other text by a space (ruling
    # out false positives).
    stripped_haystack = haystack
    while (needle_pos := stripped_haystack.find(needle)) > -1:
        needle_end = needle_pos + needle_final_pos
        stripped_haystack_len = len(stripped_haystack)
        stripped_haystack_final_pos = stripped_haystack_len - 1
        # Needs room for a space on the right.
        max_pos = stripped_haystack_final_pos - 1
        # needle_pos cannot be in first position.
        # Else, there will be no room for space
        # before needle_pos. Likewise, needle_end
        # can't be at the end of stripped_haystack.
        # Else, it can't have a space to its right.
        if needle_pos > 0 and needle_end <= max_pos:
            if (
                stripped_haystack[needle_end + 1] in string.whitespace
                and stripped_haystack[needle_pos - 1] in string.whitespace
            ):
                return True
            if (
                stripped_haystack[needle_end + 1] in string.whitespace
                and stripped_haystack[needle_pos - 1] in string.digits
            ):
                return True
        # Remove False unit from haystack.
        haystack_list = list(stripped_haystack)
        incr = 0
        while incr <= needle_end:
            del haystack_list[0]
            incr += 1
        stripped_haystack = "".join(haystack_list)

    return False
