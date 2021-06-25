# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

from modules import common
from modules import msg_handler
import csv
import string
import sys

AXELOR_CSV_COLUMNS = [
    "procurementMethodSelect",
    "purchasesUnit_importId",
    "importId",
    "productSubTypeSelect",
    "purchaseCurrency_importId",
    "productTypeSelect",
    "salePrice",
    "picture_importId",
    "managPriceCoef",
    "purchasePrice",
    "defaultSupplierPartner_importId",
    "internalDescription",
    "salesUnit_importId",
    "name",
    "productFamily_importId",
    "code",
    "description",
    "productCategory_importId",
    "saleSupplySelect",
    "fullName",
    "saleCurrency_importId",
]

# A seperate function is required for finding unit
# shorthands in strings, as some shorthand forms
# can be one character long. Need to ensure it
# is shortly after a number.
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
                subsection = []
                for incr in range(needle_len):
                    if index + incr < haystack_len:
                        subsection += haystack[index + incr]
                    else:
                        break
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


def get_name(name):
    global used_product_names
    if name in used_product_names:
        msg_handler.warning(
            string.Template(
                "Product name $name has already been defined in $id."
            ).substitute(name=name, id=msg_handler.get_xlsx_id(input_file, ws_name)),
        )
    return name


def get_descript(descript):
    return descript


def get_intern_descript(intern_descript):
    return intern_descript


def get_fam_id(cell_val):
    fam_id = -1
    for prod_fam in common.axelor_product_families:
        if prod_fam == cell_val:
            fam_id = common.axelor_product_families[cell_val]
            break
    if fam_id == -1:
        for prod_fam in common.axelor_family_shorthand:
            fam_short = common.axelor_family_shorthand[prod_fam]
            if fam_short in cell_val:
                fam_id = common.axelor_product_families[prod_fam]
                break
    if fam_id == -1:
        fam_id = common.axelor_product_families[common.fallback_family]
    return fam_id


def get_cat_id(cell_val):
    cat_id = -1
    for prod_cat in common.axelor_product_categories:
        if cat_id == cell_val:
            cat_id = common.axelor_product_categories[cell_val]
            break
    if cat_id == -1:
        for prod_cat in common.axelor_category_shorthand:
            cat_short = common.axelor_category_shorthand[prod_cat]
            if cat_short in cell_val:
                cat_id = common.axelor_product_categories[cell_val]
                break
    if cat_id == -1:
        cat_id = common.axelor_product_categories[common.fallback_category]
    return cat_id


code_incr = {}


def gen_code(cell_val):
    code = ""
    cat_id = get_cat_id(cell_val)
    cat = ""
    cat_short = ""
    fam_id = get_fam_id(cell_val)
    fam_short = ""
    fam = ""
    for category in common.axelor_product_categories:
        if common.axelor_product_categories[category] == cat_id:
            cat = category
            cat_short = common.axelor_category_shorthand.get(cat, "")
            break
    for family in common.axelor_product_families:
        if common.axelor_product_families[family] == fam_id:
            fam = family
            fam_short = common.axelor_family_shorthand.get(fam, "")
            break
    if cat == common.fallback_category:
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
    key = code
    cur_code_incr = code_incr.get(key, "0000")
    code_incr[key] = cur_code_incr
    code = code + "-" + cur_code_incr
    # Need to increment for next time.
    code_incr_int = int(cur_code_incr)
    code_incr_int += 1
    if code_incr_int >= 1000:
        code_incr[key] = str(code_incr_int)
    elif code_incr_int >= 100:
        code_incr[key] = "0" + str(code_incr_int)
    elif code_incr_int >= 10:
        code_incr[key] = "0" + "0" + str(code_incr_int)
    else:
        code_incr[key] = "0" + "0" + "0" + str(code_incr_int)
    return code


def get_code(cell_val):
    # When the force-custom-code
    # argument has been passed,
    # check if a "code" header exists.
    code = ""
    if common.force_custom_code:
        for col_name in xlsx_header_location:
            if col_name.upper() == "CODE":
                code = cell_val
    if len(code) == 0:
        code = gen_code(cell_val)
    return code


def get_product_type(cell_val):
    prod_type = ""
    for product_type in common.axelor_product_types:
        if (
            product_type in cell_val
            or common.axelor_product_types[product_type] in cell_val
        ):
            prod_type = common.axelor_product_types[product_type]
    if len(prod_type) == 0:
        prod_type = common.axelor_product_types[common.fallback_type]
    return prod_type


def get_unit(cell_val):
    unit = ""
    for ax_unit in common.axelor_units:
        if ax_unit in cell_val:
            unit = ax_unit
            break
        if ax_unit in common.axelor_units_shorthand and find_unit_shorthand(
            cell_val, common.axelor_units_shorthand[ax_unit]
        ):
            unit = ax_unit
            break
    if len(unit) == 0:
        unit = common.fallback_unit
    unit_id = common.axelor_units[unit]
    return unit_id


def get_price(cell_val):
    price_str = ""
    price = 0.00
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
            ).substitute(id=msg_handler.get_xlsx_id(input_file, ws_name), val=cell_val)
        )
        price_str = "0.00"
    price = float(price_str)
    return price


# This maps AXELOR_CSV_COLUMN names to
# functions that will return a valid value
# to be placed in a string.
CSV_FUNCTION_MAP = {
    "name": get_name,
    "description": get_descript,
    "internalDescription": get_intern_descript,
    "productFamily_importId": get_fam_id,
    "productCategory_importId": get_cat_id,
    "code": get_code,
    "productTypeSelect": get_product_type,
    "salesUnit_importId": get_unit,
    "purchasesUnit_importId": get_unit,
    "salePrice": get_price,
    "purchasePrice": get_price,
}

csv_row = {}

# Columns start at 1.
col_incr = 1
input_file = ""
ws_name = ""
max_col = 0
xlsx_header_location = {}
# header_location is the same as xlsx_header_location
# except it uses the Axelor column names.
header_location = {}

used_product_names = []


def file_ws_init(local_file, local_ws, local_max_col):
    global input_file
    global ws_name
    global max_col
    global col_incr
    global xlsx_header_location
    global header_location
    input_file = local_file
    ws_name = local_ws
    max_col = local_max_col
    col_incr = 1
    xlsx_header_location.clear()
    header_location.clear()
    for used_column in CSV_FUNCTION_MAP:
        if used_column not in common.map_dict[(input_file, ws_name)]:
            msg_handler.warning(
                f"column {used_column} is in map file, but is not handled."
            )


def set_header_location(key, val):
    global xlsx_header_location
    global header_location
    if key in xlsx_header_location:
        msg_handler.warning(
            string.Template(
                "column $col at position $col_pos is the same as at $prev_col_pos earlier in $id."
            ).substitute(
                col=key,
                col_pos=str(val),
                prev_col_pos=str(xlsx_header_location[key]),
                id=msg_handler.get_xlsx_id(input_file, ws_name),
            )
        )
    elif key not in common.map_dict[(input_file, ws_name)].values():
        msg_handler.warning(
            string.Template("column $col from $id will be ignored.").substitute(
                col=key, id=msg_handler.get_xlsx_id(input_file, ws_name)
            )
        )
    else:
        xlsx_header_location[key] = val
        # Not all Axelor CSV columns are used, so it would be more
        # efficant to use common.map_dict.
        for mapped_axelor_column in common.map_dict[(input_file, ws_name)]:
            if common.map_dict[(input_file, ws_name)][mapped_axelor_column] == key:
                header_location[mapped_axelor_column] = val


def main(val):
    global col_incr
    global csv_row
    str_val = ""
    if val is not None:
        # Force val to be string.
        str_val = str(val)
    for header in header_location:
        if header_location[header] == col_incr:
            csv_row[header] = CSV_FUNCTION_MAP[header](str_val)
    col_incr = col_incr + 1
    if col_incr > max_col:
        col_incr = 1
        commit_row()


def commit_headers():
    csv_out = csv.writer(sys.stdout, dialect="excel")
    csv_out.writerow(AXELOR_CSV_COLUMNS)


import_id_incr = 0


def commit_row():
    global csv_row
    global import_id_incr
    # Handle special cases.
    csv_row["fullName"] = "[" + csv_row["code"] + "] " + csv_row["name"]
    import_id_incr += 1
    csv_row["importId"] = import_id_incr

    # Make sure all undefined columns are blank.
    for ax_column in AXELOR_CSV_COLUMNS:
        if ax_column not in csv_row:
            csv_row[ax_column] = ""

    # Enforce a consistant ordering.
    row_list = []
    for ax_column in AXELOR_CSV_COLUMNS:
        row_list += [csv_row[ax_column]]

    csv_out = csv.writer(sys.stdout, dialect="excel")
    csv_out.writerow(row_list)
    csv_row.clear()
