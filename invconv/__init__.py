# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import importlib

# Import everything from ax-invconv so
# that all functions in ax-invconv.py
# can be accessed directly in __init__.py
# For example, invconv.main() as opposed
# to invconv.ax-invconv.main().
main_module = importlib.import_module("invconv.ax-invconv")
for attr in dir(main_module):
    if attr not in globals():
        globals()[attr] = getattr(main_module, attr)
