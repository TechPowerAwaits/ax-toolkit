#!/usr/bin/env python3

# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import argparse
import os.path

from loguru import logger
import progress.bar

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

    # Convert input file to Axelor-compatible CSV.
    logic.commit_headers()
    with progress.bar.IncrementalBar(
        message="Generating output",
        max=max_num_oper,
        suffix="%(index)d/%(max)d ETA: %(eta_td)s",
    ) as progress_bar:
        while (parser_tuple := data_list.parser()) is not None:
            filename, sectionname, header_list, content = parser_tuple
            logic.init(filename, sectionname, header_list)
            logic.main(content)
            progress_bar.next()


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
    parser_dict = vars(parser.parse_args())
    return parser_dict


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

if __name__ == "__main__":
    main()
