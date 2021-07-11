# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

# Generic utilites that can be used outside axm.

# This is useful when you have some sort of
# structure and you want to know exactly what
# it is. Returns "list" when it is a list,
# "dict" when it is a simple dictionary,
# "dict-list" when a dictionary contains
# lists as its value, and "dict-dict" when
# a dictionary contains another dictionary.
def get_table_type(table):
    table_type = ""
    if isinstance(table, list):
        table_type = "list"
    if isinstance(table, dict):
        key_list = list(table.keys())
        if len(key_list) == 0:
            table_type = "dict"
        else:
            # Use a key to test what
            # is inside the dictionary.
            test_key = key_list[0]
            test_result = table[test_key]
            # Assume that if something does
            # not have "__iter__", it must be
            # a regular variable, and therefore,
            # the dict is normal.
            if (
                isinstance(test_result, (str, int, float, bool))
                or test_result is None
                or not hasattr(test_result, "__iter__")
            ):
                table_type = "dict"
            elif isinstance(test_result, list):
                table_type = "dict-list"
            elif isinstance(test_result, dict):
                table_type = "dict-dict"
            else:
                pass
    return table_type


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


def reset_eof(axm_fptr):
    global stream_pos
    stream_pos = None
    axm_fptr.seek(0)


# This function acts like split(), except it removes any whitespace
# at the beginning and ends of the strings.
def split_n_strip(string, sep):
    split_list = []
    tmp_list = []
    if len(string) == 0:
        split_list.append("")
    else:
        for index_char in enumerate(string):
            index = index_char[0]
            char = index_char[1]
            if char == sep:
                if index == 0:
                    split_list.append("")
                else:
                    split_list.append("".join(tmp_list).strip())
                tmp_list.clear()
            else:
                tmp_list.append(char)
        # Need to add all the text after the last seperator.
        split_list.append("".join(tmp_list).strip())
    return split_list
