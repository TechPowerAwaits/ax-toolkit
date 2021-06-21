# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD
from modules import invconv_ini
from modules import msg_handler
import string

axelor_family_shorthand = {}
axelor_product_categories = {}
axelor_category_shorthand = {}
axelor_product_families = {}
axelor_product_types = []
axelor_units = {}
axelor_units_shorthand = {}
max_unit_shorthand = 0
fallback_category = ""
fallback_family = ""
fallback_type = ""
fallback_unit = ""

# Mapping between Axelor columns and input columns.
map_dict = {}
force_custom_code = False

SUPPORTED_FORMAT_VER = 1


def init(fptr):
    data_parser = invconv_ini.data_parser
    data_parser.read_file(fptr)

    global axelor_family_shorthand
    global axelor_product_categories
    global axelor_category_shorthand
    global axelor_product_families
    global axelor_product_types
    global axelor_units
    global axelor_units_shorthand
    global max_unit_shorthand
    global fallback_category
    global fallback_family
    global fallback_type
    global fallback_unit

    data_format_version = data_parser.getint("INFO", "INVCONV_FORMAT")
    if data_format_version != SUPPORTED_FORMAT_VER:
        msg_handler.error(
            string.Template(
                "FE: Data format version $format_ver is unsupported"
            ).substitute(format_ver=data_format_version)
        )
    for key in data_parser["AXELOR_PRODUCT_CATEGORIES"]:
        axelor_product_categories[key] = int(
            data_parser["AXELOR_PRODUCT_CATEGORIES"][key]
        )
        if key in data_parser["AXELOR_PRODUCT_CATEGORIES_ABREV"]:
            axelor_category_shorthand[key] = data_parser[
                "AXELOR_PRODUCT_CATEGORIES_ABREV"
            ][key]
    for key in data_parser["AXELOR_PRODUCT_FAMILIES"]:
        axelor_product_families[key] = int(data_parser["AXELOR_PRODUCT_FAMILIES"][key])
        if key in data_parser["AXELOR_PRODUCT_FAMILIES_ABREV"]:
            axelor_family_shorthand[key] = data_parser["AXELOR_PRODUCT_FAMILIES_ABREV"][
                key
            ]
    for key in data_parser["AXELOR_PRODUCT_TYPES"]:
        axelor_product_types += [key]
    for key in data_parser["AXELOR_UNITS"]:
        axelor_units[key] = data_parser["AXELOR_UNITS"][key]
        if key in data_parser["AXELOR_UNITS_ABREV"]:
            axelor_units_shorthand[key] = data_parser["AXELOR_UNITS_ABREV"][key]
    fallback_category = data_parser.get("CONSTANTS", "AXELOR_PRODUCT_CATEGORIES")
    fallback_family = data_parser.get("CONSTANTS", "AXELOR_PRODUCT_FAMILIES")
    fallback_type = data_parser.get("CONSTANTS", "AXELOR_PRODUCT_TYPES")
    fallback_unit = data_parser.get("CONSTANTS", "AXELOR_UNITS")
    max_unit_shorthand = data_parser.get("CONSTANTS", "MAX_UNIT_SHORTHAND")
