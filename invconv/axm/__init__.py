# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

# Automatically bring in all modules within the package.
try:
    import axm.command as command
    import axm.common as common
    import axm.exceptions as exceptions
    import axm.operator as operator
    import axm.output as output
    import axm.parser as parser
    import axm.scheduler as scheduler
    import axm.struct as struct
    import axm.utils as utils
except ModuleNotFoundError:
    import invconv.axm.command as command
    import invconv.axm.common as common
    import invconv.axm.exceptions as exceptions
    import invconv.axm.operator as operator
    import invconv.axm.output as output
    import invconv.axm.parser as parser
    import invconv.axm.scheduler as scheduler
    import invconv.axm.struct as struct
    import invconv.axm.utils as utils
