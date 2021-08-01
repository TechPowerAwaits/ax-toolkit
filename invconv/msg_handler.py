# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import os
import sys
import time

from loguru import logger

try:
    import common
except ModuleNotFoundError:
    import invconv.common as common

# Default log handler
# (included with loguru)
DEFAULT_ID = 0

# Default error code
# to exit with if user
# decides to exit script
# during is_continue().
USER_ERROR_CODE = 2

# A filter is needed to make sure only one level is used
# per sink.
def _lev_filter(lev):
    def _filter(record):
        required_lev = lev
        if required_lev == record["level"].name:
            return True
        return False

    return _filter


def init():
    # Default loguru handler sends everything to stderr,
    # which is not desired. Rather only errors and
    # critical errors should be outputted to stderr.
    logger.remove(DEFAULT_ID)

    # Functions are needed to set the format of
    # error messages sent to stderr.
    def error_str(record):
        error_list = []
        # To get the attention of the user.
        PANIC_TIMES = 6
        LINE_BREAK_TOP = 3
        LINE_BREAK_BOTTOM = 2

        line_break_incr = 0
        while line_break_incr < LINE_BREAK_TOP:
            error_list.append(os.linesep)
            line_break_incr += 1

        incr = 0
        while incr < PANIC_TIMES:
            # Try to avoid having an extra space at
            # the end.
            if incr > 0:
                error_list.append(" ")
            error_list.append("PANIC!")
            incr += 1

        line_break_incr = 0
        while line_break_incr < LINE_BREAK_BOTTOM:
            error_list.append(os.linesep)
            line_break_incr += 1
        error_list.append(record["message"])
        error_list.append(os.linesep)
        return "".join(error_list)

    # Errors resulting from other (non-fatal) errors
    # corresponds to a new level: failure.
    logger.level("FAILURE", no=35, color="<red>", icon="!")

    # The amount of details provided depends on if debugging is enabled.
    if common.is_debug:
        logger.add(
            sys.stderr,
            backtrace=True,
            diagnose=True,
            format="{message}",
            filter=_lev_filter("DEBUG"),
            level="DEBUG",
        )
    logger.add(
        sys.stderr,
        backtrace=common.is_debug,
        diagnose=common.is_debug,
        format=error_str,
        filter=_lev_filter("ERROR"),
        level="ERROR",
    )
    logger.add(
        sys.stderr,
        backtrace=common.is_debug,
        diagnose=common.is_debug,
        format="{level}: {message}",
        filter=_lev_filter("FAILURE"),
        level="FAILURE",
    )
    logger.add(
        sys.stderr,
        backtrace=True,
        diagnose=common.is_debug,
        filter=_lev_filter("CRITICAL"),
        level="CRITICAL",
    )


# Enables everything to get
# logged to a file.
def set_log(logfile):
    # Debug messages should not even be sent to log file
    # unless debugging is enabled.
    def filter_debug(record):
        if not common.is_debug:
            if record["level"].name == "DEBUG":
                return False
        return True

    logger.add(
        logfile,
        backtrace=True,
        catch=True,
        diagnose=common.is_debug,
        filter=filter_debug,
        errors="replace",
    )

    # Add script name and version to log.
    ver_path = os.path.join(os.path.pardir, "VERSION")
    try:
        with open(ver_path, "r") as version_file:
            logger.info(version_file.readline())
    except FileNotFoundError:
        logger.info("Unknown Script")

    # Add to log if debug mode is enabled.
    if common.is_debug:
        logger.info("Debug Mode has been enabled.")


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


# Asks the user if they want to terminate the script
# (typically done if a non-critical error has been
# reached).
def does_continue():
    print("Do you want to terminate the script? [y/n] > ", end="", file=sys.stderr)
    response = input()
    if response.lower() == "y" or response.lower() == "yes":
        logger.info("Script has not been continued.")
        sys.exit(USER_ERROR_CODE)
    print(os.linesep, os.linesep, end="", file=sys.stderr)


# Usually used within error or warning messages.
# file_section is a tuple containing the file path
# and section name, while section_type gives the
# section divider a name. For example, providing
# "WS" as section_type with a file path of "file"
# and a section of test would result in file WS: test.
def get_id(file_section, section_type="SECTION"):
    filepath, sectionname = file_section
    upper_section_type = section_type.upper() + ":"
    return f"{filepath} {upper_section_type} {str(sectionname)}"
