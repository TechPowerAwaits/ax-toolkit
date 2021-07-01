# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import os.path
import string
import sys
import time

# Log file is defined here so that a file pointer
# can repeatedly be created and destroyed. This is needed
# because if the script crashes, the file won't be properly
# closed otherwise.
log_file = ""


def get_default_logname():
    logname = f"invconv-{time.strftime('%m-%d-%Y_%H-%M-%S')}.log"
    incr = 1
    while os.path.exists(logname):
        # First run
        if incr == 1:
            logname += "_" + str(incr)
        else:
            # Since its run once already,
            # replace num.
            prev_incr = incr - 1
            logname.removesuffix(str(prev_incr))
            logname += str(incr)
        incr += 1
    return logname


def init(filepath):
    global log_file
    log_file = filepath


def error(error_str):
    # To get the attention of the user.
    FATAL_CODE = 2
    print("\n\n\nFatal Error!!!\n\n", end="", file=sys.stderr)
    print(error_str, file=sys.stderr)
    with open(log_file, "a", errors="replace") as log_fptr:
        print(f"FE: {error_str}", file=log_fptr)
    sys.exit(FATAL_CODE)


# Usually used within error or warning messages.
def get_xlsx_id(filepath, ws_name):
    return filepath + " WS: " + str(ws_name)


def info(info_str):
    with open(log_file, "a", errors="replace") as log_fptr:
        print(f"Info: {info_str}", file=log_fptr)


def input_fail(fail_str):
    # This doesn't need a new line as the panic() function already
    # made new lines and will do so again.
    print(f"Input invalid: {fail_str}.", end="", file=sys.stderr)
    with open(log_file, "a", errors="replace") as log_fptr:
        print(f"Input invalid: {fail_str}.", file=log_fptr)


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
    with open(log_file, "a", errors="replace") as log_fptr:
        print(f"Panic: {issue_str}", file=log_fptr)

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
    with open(log_file, "a", errors="replace") as log_fptr:
        print(
            string.Template("Panic Response: $input").substitute(input=user_input),
            file=log_fptr,
        )
    return user_input


def warning(warn_str):
    with open(log_file, "a", errors="replace") as log_fptr:
        print(f"Warning: {warn_str}", file=log_fptr)
