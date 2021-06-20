# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import sys


def error(error_str):
    # To get the attention of the user.
    FATAL_CODE = 2
    print("\n\n\nFatal Error!!!\n\n", end="", file=sys.stderr)
    print(error_str, end="", file=sys.stderr)
    sys.exit(FATAL_CODE)


# Usually used within error or warning messages.
def get_xlsx_id(filepath, ws_name):
    return filepath + " WS: " + str(ws_name)


def info(info_str):
    print(f"Info: {info_str}", file=sys.stderr)


def panic(issue_str):
    # To get the attention of the user.
    PANIC_TIMES = 6
    PANIC_CODE = 3
    print("\n\n\n", end="", file=sys.stderr)
    incr = 0
    while incr < PANIC_TIMES:
        print("PANIC! ", end="", file=sys.stderr)
        incr += 1
    print("\n\n", end="", file=sys.stderr)
    print(issue_str, file=sys.stderr)

    print("Do you want to terminate the script? [y/n] > ", end="", file=sys.stderr)
    response = input()
    if response.lower() == "y" or response.lower() == "yes":
        sys.exit(PANIC_CODE)


def panic_user_input(issue_str, user_prompt):
    panic(issue_str)
    print("\n\n", end="", file=sys.stderr)
    print(user_prompt + " > ", end="", file=sys.stderr)
    user_input = input()
    print("\n", end="", file=sys.stderr)
    return user_input


def warning(warn_str):
    print(f"Warning: {warn_str}", file=sys.stderr)
