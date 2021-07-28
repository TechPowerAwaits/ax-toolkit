#!/usr/bin/env python3

# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import argparse
import os
import sys

from alive_progress import alive_bar
from loguru import logger

# Script can also be used as a module.
try:
    import axm
    import builtin_types
    import common
    import ftype
    from exceptions import InvconvArgumentError
    import logic
    import msg_handler
except ModuleNotFoundError:
    # Disable logging by default
    # when imported in another script.
    logger.disable("invconv")
    import invconv.axm as axm
    import invconv.builtin_types as builtin_types
    import invconv.common as common
    import invconv.ftype as ftype
    from invconv.exceptions import InvconvArgumentError
    import invconv.logic as logic
    import invconv.msg_handler as msg_handler


@logger.catch(level="CRITICAL")
def main(arg_dict=None):
    if arg_dict is None:
        arg_dict = get_arg_dict()
    if not isinstance(arg_dict, dict):
        raise InvconvArgumentError
    try:
        input_files = arg_dict["input"]
        map_file = arg_dict["map_file"]
        common.is_debug = arg_dict["debug"]
        file_type = arg_dict["type"]
        common.output_file_path = get_proper_output(arg_dict["output"])
    except KeyError:
        raise InvconvArgumentError
    # Set up logger.
    # (If any errors occured before
    # this point, it would be handled
    # by loguru's default log handler.)
    msg_handler.init()
    msg_handler.set_log(arg_dict["log_file"])
    # Takes the arg_dict and sets fallback
    # values in the script based on what the
    # user has set.
    set_fallback(arg_dict)

    # Run the function for the proper file type.
    type_func = ftype.get_func(file_type)
    data_list = type_func(input_files)

    # Figure out the proper mapping between Axelor CSV and input headers.
    axm.parser.init(data_list.headers())
    with open(map_file) as map_fptr:
        while not axm.utils.is_eof(map_fptr):
            axm.parser.parse(map_fptr)
    axm.parser.finalize()

    # Setup progress bar.
    max_num_oper = 0
    for data_tuple in data_list:
        max_num_oper += data_tuple.num_oper
    # Check if unicode is supported and set
    # progress bar theme based on it.
    bar_theme_settings = {"bar": "smooth", "spinner": "waves"}
    if sys.getdefaultencoding() != "utf-8" or os.name == "nt":
        bar_theme_settings = {"bar": "classic2", "spinner": "classic"}

    # Convert input file to Axelor-compatible CSV.
    logic.commit_headers()
    with alive_bar(
        max_num_oper, title="Generating output", **bar_theme_settings
    ) as progress_bar:
        while (parser_tuple := data_list.parser()) is not None:
            filename, sectionname, header_list, content = parser_tuple
            progress_bar.text(msg_handler.get_id((filename, sectionname)))
            logic.init(filename, sectionname, header_list)
            logic.main(content)
            progress_bar()


def get_arg_dict():
    parser = argparse.ArgumentParser(
        description="Converts inventory lists to a Axelor-compatible CSV format",
        epilog="Licensed under the 0BSD.",
        add_help=False,
    )
    parser.add_argument("-d", "--data-file", default="demo.ini", help="INI data file")
    data_file = parser.parse_known_args()[0].data_file
    with open(data_file) as data_fptr:
        common.init(data_fptr)

    parser.add_argument("-m", "--map-file", default="default.axm", help="AXM map file")
    parser.add_argument(
        "-l",
        "--log-file",
        default=msg_handler.get_default_logname(),
        help="File to store messages",
    )
    parser.add_argument("-D", "--debug", action="store_true", help="Enables debugging")
    parser.add_argument(
        "-h", "--help", action="help", help="show this help message and exit"
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument(
        "-t",
        "--type",
        default=ftype.get_default(),
        choices=ftype.list_types(),
        help="The type of file that is being imported",
    )

    # Looks at the fallback-related arguments defined in data file
    # and officially adds it as an argument.
    for section_name, arg_tuple in common.arg_dict.items():
        short_arg = arg_tuple.short
        long_arg = arg_tuple.long
        help_text = arg_tuple.help
        parser.add_argument(
            short_arg,
            long_arg,
            default=common.fallback[section_name],
            choices=common.meta_table[section_name],
            help=help_text,
        )

    parser.add_argument("input", nargs="+", help="Input file(s)")
    parser.add_argument(
        "-o", "--output", default="", help="File or path to place csv file"
    )
    parser_dict = vars(parser.parse_args())
    return parser_dict


def get_proper_output(output_path):
    output_file = ""
    if common.is_debug:
        if output_path.endswith("stdout"):
            output_file = sys.stdout
        if output_path.endswith("stderr") or not output_path:
            output_file = sys.stderr
        # If output_file has something in it, return right away
        # to avoid InvconvArgumentError.
        if output_file:
            return output_file
    # Checks if a file already exists (which gets replaced) or if
    # ".csv" exists in output_path (in which case, file gets created).
    if os.path.isfile(output_path) or output_path.endswith(".csv"):
        output_file = output_path
        # Replace the file if it already existed.
        with open(output_file, "w", newline=""):
            pass
    elif os.path.isdir(output_path):
        output_file = os.path.join(output_path, common.axelor_csv_type.title() + ".csv")
    else:
        raise InvconvArgumentError
    return output_file


def set_fallback(arg_dict):
    # Looks at the fallback-related arguments again and
    # replaces all appropriate values in the fallback dict
    # with the user-provided values. If the user didn't override
    # the default fallback values, then the fallback values
    # in the dict will be replaced with the values it currently has.
    for section_name, arg_tuple in common.arg_dict.items():
        long_arg = arg_tuple.long
        key = long_arg.removeprefix("--").replace("-", "_")
        common.fallback[section_name] = arg_dict[key]


__version__ = "Unknown"
ver_path = os.path.join(os.path.pardir, "VERSION")
try:
    with open(ver_path, "r") as version_file:
        __version__ = version_file.readline()
except FileNotFoundError:
    pass

# Fixes an issue with Windows where the
# progress bar infinitely scrolls up.
# (Issue #97 on alive-progress GitHub)
if os.name == "nt":
    os.system("")

if __name__ == "__main__":
    main()
