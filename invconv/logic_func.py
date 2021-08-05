# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

"""Contains built-in logic functions."""

import collections
import string

from loguru import logger

try:
    import axm
    import common
    import logic_utils
    import msg_handler
except ModuleNotFoundError:
    import invconv.axm as axm
    import invconv.common as common
    import invconv.logic_utils as logic_utils
    import invconv.msg_handler as msg_handler

used_product_names = set()


def get_name(name):
    global used_product_names
    if name in used_product_names:
        logger.warning(
            string.Template(
                'Product name "$name" has already been defined in $id.'
            ).substitute(
                name=name,
                id=msg_handler.get_id((common.file_name, common.section_name)),
            )
        )
    used_product_names.add(name)
    return name


if axm.output.get_func("name") is None:
    axm.output.set_func("name", get_name)


def get_group_id_gen(table_name):
    def get_group_id(cell_val):
        group_id = -1
        for group_name in common.meta_table[table_name]:
            if group_name.title() == cell_val.title():
                group_id = common.meta_table[table_name][group_name]
                break
        if (
            group_id == -1
            and (abrev_table := f"{table_name}_abrev") in common.meta_table
        ):
            for group_name in common.meta_table[abrev_table]:
                group_short = common.meta_table[abrev_table][group_name]
                if logic_utils.find_shorthand(cell_val.upper(), group_short.upper()):
                    group_id = common.meta_table[table_name][group_name]
                    break
        if group_id == -1:
            group_id = common.meta_table[table_name][common.fallback[table_name]]

        return group_id

    return get_group_id


get_fam_id = get_group_id_gen("axelor_product_families")

if axm.output.get_func("productFamily_importId") is None:
    axm.output.set_func("productFamily_importId", get_fam_id)

get_cat_id = get_group_id_gen("axelor_product_categories")

if axm.output.get_func("productCategory_importId") is None:
    axm.output.set_func("productCategory_importId", get_cat_id)


# Keeps track of the name used for
# the code and the row_incr used at
# the time it was last updated. If
# the row_incr has changed since then,
# cur_val will be incremented.
used_code_nums = {}
CodeTracker = collections.namedtuple("CodeTracker", ("row_incr", "cur_val"))


def gen_code(cell_val):
    global used_code_nums
    code = ""
    cat_id = get_cat_id(cell_val)
    cat = ""
    cat_short = ""
    fam_id = get_fam_id(cell_val)
    fam_short = ""
    fam = ""
    for category in common.meta_table["axelor_product_categories"]:
        if common.meta_table["axelor_product_categories"][category] == cat_id:
            cat = category
            cat_short = common.meta_table["axelor_product_categories_abrev"].get(
                cat, ""
            )
            break
    for family in common.meta_table["axelor_product_families"]:
        if common.meta_table["axelor_product_families"][family] == fam_id:
            fam = family
            fam_short = common.meta_table["axelor_product_families_abrev"].get(fam, "")
            break
    # If category value is fallback, use family instead and
    # vice-versa.
    if cat == common.fallback["axelor_product_categories"]:
        if fam_short:
            code = fam_short.upper().replace(" ", "_")
    else:
        if cat_short:
            code = cat_short.upper().replace(" ", "_")
    if not code:
        if not common.csv_row.get("name", ""):
            code = "INVCONV"
        else:
            code = common.csv_row["name"].upper().replace(" ", "_")
    # Start cur_val at zero.
    if code not in used_code_nums:
        used_code_nums[code] = CodeTracker(row_incr=common.row_incr, cur_val=0)
    # If row_incr in CodeTracker isn't equal to current row_incr,
    # increment cur_val.
    if used_code_nums[code].row_incr != common.row_incr:
        used_code_nums[code] = CodeTracker(
            row_incr=common.row_incr, cur_val=used_code_nums[code].cur_val + 1
        )
    # A list is used to make code more portable.
    tmp_code_list = [code, "-"]
    # cur_val starting at zero is used in code.
    # Numbers under 1000 are prepended with zeros.
    cur_val = used_code_nums[code].cur_val
    if cur_val >= 1000:
        pass
    elif cur_val >= 100:
        tmp_code_list.append("0")
    elif cur_val >= 10:
        tmp_code_list.append("00")
    else:
        tmp_code_list.append("000")
    tmp_code_list.append(str(cur_val))
    full_code = "".join(tmp_code_list)
    return full_code


if axm.output.get_func("code") is None:
    axm.output.set_func("code", gen_code)


def get_product_type(cell_val):
    prod_type = ""
    for product_type in common.meta_table["axelor_product_types"]:
        if (
            product_type in cell_val
            or common.meta_table["axelor_product_types"][product_type] in cell_val
        ):
            prod_type = common.meta_table["axelor_product_types"][product_type]
            break
    if not prod_type:
        prod_type = common.meta_table["axelor_product_types"][
            common.fallback["axelor_product_types"]
        ]
    return prod_type


if axm.output.get_func("productTypeSelect") is None:
    axm.output.set_func("productTypeSelect", get_product_type)


def get_unit(cell_val):
    unit = ""
    for ax_unit in common.meta_table["axelor_units"]:
        if ax_unit.title() in cell_val.title():
            unit = ax_unit
            break
        if (
            not unit
            and ax_unit in common.meta_table["axelor_units_abrev"]
            and logic_utils.find_unit_shorthand(
                cell_val, common.meta_table["axelor_units_abrev"][ax_unit]
            )
        ):
            unit = ax_unit
            break
    if not unit:
        unit = common.fallback["axelor_units"]
    unit_id = common.meta_table["axelor_units"][unit]
    return unit_id


if axm.output.get_func("salesUnit_importId") is None:
    axm.output.set_func("salesUnit_importId", get_unit)
if axm.output.get_func("purchasesUnit_importId") is None:
    axm.output.set_func("purchasesUnit_importId", get_unit)


def get_price(cell_val):
    price_list = []
    # Ensure that only one decimal will
    # be in price.
    one_dec_point = False
    # Keep track over whether digits are being
    # found or not.
    found_digit = False

    for char in cell_val:
        if char in string.digits:
            price_list.append(char)
            found_digit = True
        # Only append decimal point if one was not found earlier
        # and if digits were found before.
        elif char == "." and found_digit and not one_dec_point:
            price_list.append(char)
            one_dec_point = True
        else:
            # Ensure a decimal isn't the last
            # character in list.
            if found_digit:
                if price_list[-1] == ".":
                    del price_list[-1]
                break

    # price_str could be empty or contain an actual
    # price.
    price_str = "".join(price_list)
    if not price_str:
        logger.warning(
            string.Template(
                'Cell in $id has "$val" and not cost. Defaulting to 0.00.'
            ).substitute(
                id=msg_handler.get_id((common.file_name, common.section_name)),
                val=cell_val,
            )
        )
        price_str = "0.00"
    return price_str


if axm.output.get_func("salePrice") is None:
    axm.output.set_func("salePrice", get_price)
if axm.output.get_func("purchasePrice") is None:
    axm.output.set_func("purchasePrice", get_price)
