# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import collections
import csv
import string

from loguru import logger

try:
    import axm
    import common
    import msg_handler
except ModuleNotFoundError:
    import invconv.axm as axm
    import invconv.common as common
    import invconv.msg_handler as msg_handler

# In some cases, functions
# might be run multiple times
# while in the same row, possibly
# skewing values. This keeps track
# of the number of rows outputted
# (starting at zero and not
# including the Axelor column row).
row_incr = 0

# A seperate function is required for units,
# as some abbreviated forms can be one character long.
# Need to ensure it is shortly after a number.
def find_unit_shorthand(haystack, needle):
    haystack_len = len(haystack)
    haystack_final_pos = haystack_len - 1
    needle_len = len(needle)
    needle_final_pos = needle_len - 1

    # Check for exact matches.
    if haystack == needle:
        return True

    # Check if unit is at end of haystack (or
    # before a period) and has a digit right
    # before it or whitespace before a digit
    # (ruling out false positives).
    needle_pos = haystack.rfind(needle)
    needle_end = needle_pos + needle_final_pos
    if needle_end == haystack_final_pos or (
        needle_end == (haystack_final_pos - 1) and haystack[haystack_final_pos] == "."
    ):
        # Ensure needle_pos has enough room for a
        # digit before it.
        if (needle_pos - 1) > -1 and haystack[needle_pos - 1] in string.digits:
            return True
        # Ensure needle_pos has enough room for a
        # digit and whitespace before it.
        if (
            (needle_pos - 2) > -1
            and haystack[needle_pos - 1] in string.whitespace
            and haystack[needle_pos - 2] in string.digits
        ):
            return True

    # Check if unit is surrounded by spaces
    # or is next to a digit and seperated
    # from other text by a space (ruling
    # out false positives).
    stripped_haystack = haystack
    while (needle_pos := stripped_haystack.find(needle)) > -1:
        needle_end = needle_pos + needle_final_pos
        stripped_haystack_len = len(stripped_haystack)
        stripped_haystack_final_pos = stripped_haystack_len - 1
        # Needs room for a space on the right.
        max_pos = stripped_haystack_final_pos - 1
        # needle_pos cannot be in first position.
        # Else, there will be no room for space
        # before needle_pos. Likewise, needle_end
        # can't be at the end of stripped_haystack.
        # Else, it can't have a space to its right.
        if needle_pos > 0 and needle_end <= max_pos:
            if (
                stripped_haystack[needle_end + 1] in string.whitespace
                and stripped_haystack[needle_pos - 1] in string.whitespace
            ):
                return True
            if (
                stripped_haystack[needle_end + 1] in string.whitespace
                and stripped_haystack[needle_pos - 1] in string.digits
            ):
                return True
        # Remove False unit from haystack.
        haystack_list = list(stripped_haystack)
        incr = 0
        while incr <= needle_end:
            del haystack_list[0]
            incr += 1
        stripped_haystack = "".join(haystack_list)

    return False


used_product_names = set()


def get_name(name):
    global used_product_names
    if name in used_product_names:
        logger.warning(
            string.Template(
                'Product name "$name" has already been defined in $id.'
            ).substitute(name=name, id=msg_handler.get_id((file_name, section_name)))
        )
    used_product_names.add(name)
    return name


def get_descript(descript):
    return descript


def get_intern_descript(intern_descript):
    return intern_descript


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
                if group_short in cell_val.upper():
                    group_id = common.meta_table[table_name][group_name]
                    break
        if group_id == -1:
            group_id = common.meta_table[table_name][common.fallback[table_name]]

        return group_id

    return get_group_id


get_fam_id = get_group_id_gen("axelor_product_families")
get_cat_id = get_group_id_gen("axelor_product_categories")


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
        if not csv_row.get("name", ""):
            code = "INVCONV"
        else:
            code = csv_row["name"].upper().replace(" ", "_")
    # Start cur_val at zero.
    if code not in used_code_nums:
        used_code_nums[code] = CodeTracker(row_incr=row_incr, cur_val=0)
    # If row_incr in CodeTracker isn't equal to current row_incr,
    # increment cur_val.
    if used_code_nums[code].row_incr != row_incr:
        used_code_nums[code] = CodeTracker(
            row_incr=row_incr, cur_val=used_code_nums[code].cur_val + 1
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


def get_product_type(cell_val):
    prod_type = ""
    for product_type in common.meta_table["axelor_product_types"]:
        if (
            product_type in cell_val
            or common.meta_table["axelor_product_types"][product_type] in cell_val
        ):
            prod_type = common.meta_table["axelor_product_types"][product_type]
            break
    if len(prod_type) == 0:
        prod_type = common.meta_table["axelor_product_types"][
            common.fallback["axelor_product_types"]
        ]
    return prod_type


def get_unit(cell_val):
    unit = ""
    for ax_unit in common.meta_table["axelor_units"]:
        if ax_unit.title() in cell_val.title():
            unit = ax_unit
            break
        if (
            not unit
            and ax_unit in common.meta_table["axelor_units_abrev"]
            and find_unit_shorthand(
                cell_val, common.meta_table["axelor_units_abrev"][ax_unit]
            )
        ):
            unit = ax_unit
            break
    if not unit:
        unit = common.fallback["axelor_units"]
    unit_id = common.meta_table["axelor_units"][unit]
    return unit_id


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
            ).substitute(id=msg_handler.get_id((file_name, section_name)), val=cell_val)
        )
        price_str = "0.00"
    return price_str


# This maps AXELOR_CSV_COLUMN names to
# functions that will return a valid value
# to be placed in a string.
CSV_FUNCTION_MAP = {
    "name": get_name,
    "description": get_descript,
    "internalDescription": get_intern_descript,
    "productFamily_importId": get_fam_id,
    "productCategory_importId": get_cat_id,
    "code": gen_code,
    "productTypeSelect": get_product_type,
    "salesUnit_importId": get_unit,
    "purchasesUnit_importId": get_unit,
    "salePrice": get_price,
    "purchasePrice": get_price,
}

csv_row = {}

file_name = None
section_name = None
# Contains the input header
# names in their proper order.
input_header_list = []
# Keeps track of the position amongst
# the input columns
pos_index = 0


def init(local_file_name, local_section_name, header_list):
    global file_name
    global section_name
    global input_header_list
    file_name = local_file_name
    section_name = local_section_name
    input_header_list = header_list


def main(val):
    global csv_row
    global pos_index
    global row_incr
    str_val = ""
    if val is not None:
        # Force val to be string.
        str_val = str(val)
    for header in common.axelor_csv_columns:
        output_str_param = [(file_name, section_name), header, str_val]
        input_col = input_header_list[pos_index]
        if header in CSV_FUNCTION_MAP:
            output_str_param.append(CSV_FUNCTION_MAP[header])
        if axm.output.is_valid_input_col((file_name, section_name), header, input_col):
            csv_row[header] = axm.output.string(*output_str_param)
    max_pos = len(input_header_list) - 1
    if pos_index == max_pos:
        pos_index = 0
        # Only commit if there is content in csv_row.
        # There won't be if a section is avoided, for instance.
        if len(csv_row) > 0:
            commit_row()
            row_incr += 1
        else:
            csv_row.clear()
    else:
        pos_index += 1


def commit_headers():
    if isinstance(common.output_file_path, str):
        with open(common.output_file_path, "a", newline="") as fptr:
            csv_out = csv.writer(fptr, dialect="excel")
            csv_out.writerow(common.axelor_csv_columns)
    else:
        csv_out = csv.writer(common.output_file_path, dialect="excel")
        csv_out.writerow(common.axelor_csv_columns)


import_id_incr = 0


def commit_row():
    global csv_row
    global import_id_incr
    # Handle special cases.
    csv_row["fullName"] = "[" + csv_row["code"] + "] " + csv_row["name"]
    import_id_incr += 1
    csv_row["importId"] = import_id_incr

    # Make sure all undefined columns are blank.
    for ax_column in common.axelor_csv_columns:
        if ax_column not in csv_row:
            csv_row[ax_column] = ""

    # Enforce a consistant ordering.
    row_list = []
    for ax_column in common.axelor_csv_columns:
        row_list.append(csv_row[ax_column])

    if isinstance(common.output_file_path, str):
        with open(common.output_file_path, "a", newline="") as fptr:
            csv_out = csv.writer(fptr, dialect="excel")
            csv_out.writerow(row_list)
    else:
        csv_out = csv.writer(common.output_file_path, dialect="excel")
        csv_out.writerow(row_list)
    csv_row.clear()
