###############
xlsx test files
###############

:001-unknown_dimensions.xlsx:
    For some reason, openpyxl can't figure out the dimensions of the
    file. It is primarly used to test whether the script still allows a
    user to manually enter the text. It also contains column names that
    aren't mapped to any Axelor column in the default.axm file. So, it
    is also useful for testing whether the script catches the lack of
    valid columns or not.

:002-script_workout.xlsx:
    This file is designed with the default functions, map file, and
    data file in mind. It contains mixed cases and other strings
    designed to try to confuse the script.

:003-blank_cols.xlsx:
    This file works with the default map and data files. It contains
    nothing special to confuse the script. Just some very basic text.
    It also contains blank cells to see if the script properly uses
    the fallback values.

:004-emoji_galore.xlsx:
    Contains valid headers for the map file, but all its content is
    emoji. The point of this file is to test if the script is going
    to crash when unicode is used in a file.
    (Platform specific result.)

:005-multiline.xlsx:
    The description column has two lines. It is meant to test how
    well the script can handle a multi-line cell.