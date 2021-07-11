# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import os.path
import string
import sys
import time

# Default error code that is returned
# in case of a fatal error.
ERROR_CODE = 2

# Default error code that is returned
# when a user exits from a panic.
PANIC_CODE = 3

# Log file is defined here so that a file pointer
# can repeatedly be created and destroyed. This is needed
# because if the script crashes, the file won't be properly
# closed otherwise.
log_file = ""


def get_default_logname():
    logname_list = []
    logname_list.append(f"invconv-{time.strftime('%m-%d-%Y_%H-%M-%S')}")
    log_ext = "log"
    incr = 1
    while os.path.exists(f"{''.join(logname_list)}.{log_ext}"):
        # First run
        if incr == 1:
            logname_list.append("_")
        else:
            # Since its run once already,
            # replace num.
            max_list_pos = len(logname_list) - 1
            del logname_list[max_list_pos]
        logname_list.append(str(incr))
        incr += 1
    logname_list.append(f".{log_ext}")
    logname = "".join(logname_list)
    return logname


def init(filepath):
    global log_file
    log_file = filepath


def error(error_str, status_code=2):
    # To get the attention of the user.
    print("\n\n\nFatal Error!!!\n\n", end="", file=sys.stderr)
    print(error_str, file=sys.stderr)
    with open(log_file, "a", errors="replace") as log_fptr:
        print(f"FE: {error_str}", file=log_fptr)
    sys.exit(status_code)


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


def panic(issue_str, status_code=PANIC_CODE):
    # To get the attention of the user.
    PANIC_TIMES = 6
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
        sys.exit(status_code)


def panic_user_input(issue_str, user_prompt, status_code=PANIC_CODE):
    panic(issue_str, status_code)
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
