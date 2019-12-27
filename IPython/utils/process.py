"""Utilities for working with external processes."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from ._process_common import getoutputerror, get_output_error_code, process_handler
import os
import shutil
from shutil import which as find_cmd  # noqa F401  replaces find_cmd
import sys
from os import system  # noqa F401  replaces system
from subprocess import CalledProcessError as FindCmdError  # noqa F401  replaces FindCmdError
from subprocess import getoutput  # noqa F401  replaces getoutput

if sys.platform == "win32":
    from ._process_win32 import arg_split, check_pid
else:
    from ._process_posix import check_pid
    from ._process_common import arg_split


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
