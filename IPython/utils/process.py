"""Utilities for working with external processes."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

# from ._process_common import getoutputerror, get_output_error_code, process_handler
import os
from os import system
import shutil
import sys

from subprocess import CalledProcessError as FindCmdError
from subprocess import check_output as getoutput

if sys.platform == "win32":
    from ._process_win32 import arg_split, check_pid
else:
    from ._process_posix import arg_split, check_pid


def find_cmd(cmd):
    """Find absolute path to executable cmd in a cross platform manner.

    This function tries to determine the full path to a command line program
    using `which` on Unix/Linux/OS X and `win32api` on Windows.  Most of the
    time it will use the version that is first on the users `PATH`.

    Warning, don't use this to find IPython command line programs as there
    is a risk you will find the wrong one.  Instead find those using the
    following code and looking for the application itself::

        import sys
        argv = [sys.executable, '-m', 'IPython']

    Parameters
    ----------
    cmd : str
        The command line program to look for.
    """
    return shutil.which(cmd)


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
