# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

"""Contains built-in file types supported by script."""

from loguru import logger

try:
    import xlsx
except ModuleNotFoundError:
    import invconv.xlsx

logger.info("Finished loading built-in types.")
