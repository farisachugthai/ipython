"""Utilities for working with external processes."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import shutil
import sys
from os import system  # noqa F401  replaces system
from shutil import which as find_cmd  # noqa F401  replaces find_cmd
from subprocess import (
    CalledProcessError as FindCmdError,
)  # noqa F401  replaces FindCmdError
from subprocess import getoutput  # noqa F401  replaces getoutput

from ._process_common import get_output_error_code, getoutputerror, process_handler, arg_split

if sys.platform == "win32":
    from ._process_win32 import check_pid
else:
    from ._process_posix import check_pid


def abbrev_cwd():
    """ Return abbreviated version of cwd, e.g. d:mydir """
    cwd = os.getcwd().replace("\\", "/")
    drivepart = ""
    tail = cwd
    if sys.platform == "win32":
        if len(cwd) < 4:
            return cwd
        drivepart, tail = os.path.splitdrive(cwd)

    parts = tail.split("/")
    if len(parts) > 2:
        tail = "/".join(parts[-2:])

    return drivepart + (cwd == "/" and "/" or tail)
