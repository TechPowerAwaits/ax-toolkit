# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD


class InvconvException(Exception):
    pass


class InvconvMissingHeaders(InvconvException):
    def __init__(self):
        self.message = "No headers were found in any input file"
        super().__init__(self.message)


class InvconvUnsupportedDataFile(InvconvException):
    def __init__(self, ver_found, ver_expect):
        self.message = f"Expected version {ver_expect}, but got {ver_found} instead"
        super().__init__(self.message)
