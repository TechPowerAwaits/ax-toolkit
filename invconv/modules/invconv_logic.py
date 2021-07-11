# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import axm.output
from modules import common
from modules import msg_handler
import csv
import string
import sys

# In some cases, functions
# might be run multiple times
# while in the same row, possibly
# skewing values. This keeps track
# of the number of rows outputted
# (starting at zero and not
# including the Axelor column row).
row_incr = 0

# A seperate function is requied for units,
# as some shorthand forms can be one character long.
# Need to ensure it is shortly after a number.
def find_unit_shorthand(haystack, needle):
    contain_num = False
    for digit in string.digits:
        if digit in haystack:
            contain_num = True
    if contain_num:
        haystack_len = len(haystack)
        needle_len = len(needle)
        found_int_or_space = False
        for index in range(haystack_len):
            if (haystack[index] in string.digits) or (
                haystack[index] in string.whitespace
            ):
                found_int_or_space = True
            if found_int_or_space:
                subsection_list = []
                for incr in range(needle_len):
                    if index + incr < haystack_len:
                        subsection_list.append(haystack[index + incr])
                    else:
                        break
                subsection = "".join(subsection_list)
                if needle in subsection:
                    # If it doesn't have a space after it or end right away,
                    # it is probably a false positive.
                    haystack_final_pos = haystack_len - 1
                    haystack_cur_pos = index + needle_len
                    if haystack_cur_pos > haystack_final_pos:
                        break
                    if haystack_cur_pos == haystack_final_pos:
                        return True
                    if haystack[haystack_cur_pos] in string.whitespace:
                        return True
                else:
                    # Reset found_int_or_space so it doesn't keep on looking
                    # for shorthand forms long after a number has been found,
                    # thus leading to a false positive.
                    found_int_or_space = False
            else:
                pass

    return False


used_product_names = set()


def get_name(name):
    global used_product_names
    if name in used_product_names:
        msg_handler.warning(
            string.Template(
                "Product name $name has already been defined in $id."
            ).substitute(
                name=name, id=msg_handler.get_xlsx_id(file_name, section_name)
            ),
        )
    used_product_names.add(name)
    return name


def get_descript(descript):
    return descript


def get_intern_descript(intern_descript):
    return intern_descript


def get_fam_id(cell_val):
    fam_id = -1
    for prod_fam in common.meta_table["axelor_product_families"]:
        if prod_fam == cell_val:
            fam_id = common.meta_table["axelor_product_families"][cell_val]
            break
    if fam_id == -1:
        for prod_fam in common.meta_table["axelor_product_families_abrev"]:
            fam_short = common.meta_table["axelor_product_families_abrev"][prod_fam]
            if fam_short in cell_val:
                fam_id = common.meta_table["axelor_product_families"][prod_fam]
                break
    if fam_id == -1:
        fam_id = common.meta_table["axelor_product_families"][
            common.fallback["axelor_product_families"]
        ]
    return fam_id


def get_cat_id(cell_val):
    cat_id = -1
    for prod_cat in common.meta_table["axelor_product_categories"]:
        if cat_id == cell_val:
            cat_id = common.meta_table["axelor_product_categories"][cell_val]
            break
    if cat_id == -1:
        for prod_cat in common.meta_table["axelor_product_categories"]:
            cat_short = common.meta_table["axelor_product_categories_abrev"][prod_cat]
            if cat_short in cell_val:
                cat_id = common.meta_table["axelor_product_categories"][prod_cat]
                break
    if cat_id == -1:
        cat_id = common.meta_table["axelor_product_categories"][
            common.fallback["axelor_product_categories"]
        ]
    return cat_id


def gen_code(cell_val):
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
    if cat == common.fallback["axelor_product_categories"]:
        if len(fam_short) > 0:
            code = fam_short.upper().replace(" ", "_")
    else:
        if len(cat_short) > 0:
            code = fam_short.upper().replace(" ", "_")
    if len(code) == 0:
        if len(csv_row.get("name", "")) == 0:
            code = "INVCONV"
        else:
            code = csv_row["name"].upper().replace(" ", "_")
    # A list is used to make code more portable.
    tmp_code_list = [code, "-"]
    # Row number starting at zero is used in code.
    # Numbers under 1000 are prepended with zeros.
    if row_incr >= 1000:
        pass
    elif row_incr >= 100:
        tmp_code_list.append("0")
    elif row_incr >= 10:
        tmp_code_list.append("00")
    else:
        tmp_code_list.append("000")
    tmp_code_list.append(str(row_incr))
    code = "".join(tmp_code_list)
    return code


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
        if ax_unit in cell_val:
            unit = ax_unit
            break
        if ax_unit in common.meta_table["axelor_units_abrev"] and find_unit_shorthand(
            cell_val, common.meta_table["axelor_units_abrev"][ax_unit]
        ):
            unit = ax_unit
            break
    if len(unit) == 0:
        unit = common.fallback["axelor_units"]
    unit_id = common.meta_table["axelor_units"][unit]
    return unit_id


def get_price(cell_val):
    price_str = ""
    for char in cell_val:
        if char in string.digits or char == ".":
            price_str += char
    # price_str could be empty or just contain dots
    # depending on the value in the cell.
    highest_index = len(price_str) - 1
    if len(price_str) == 0 or price_str.rfind(".") == highest_index:
        msg_handler.warning(
            string.Template(
                "Cell in $id has $val and not cost. Defaulting to 0.00."
            ).substitute(
                id=msg_handler.get_xlsx_id(file_name, section_name), val=cell_val
            )
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
    csv_out = csv.writer(sys.stdout, dialect="excel")
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

    csv_out = csv.writer(sys.stdout, dialect="excel")
    csv_out.writerow(row_list)
    csv_row.clear()
