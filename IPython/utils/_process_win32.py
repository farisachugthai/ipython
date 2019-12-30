"""Windows-specific implementation of process utilities.

This file is only meant to be imported by process.py, not by end-users.

Then define ``__all__`?

.. note:: This depends on pywin32.

"""

# -----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import ctypes

# stdlib
import os
import subprocess
import sys
from ctypes import POINTER, c_int
from subprocess import STDOUT
from subprocess import getoutput  # noqa F401 replaces the old getoutput func here

# our own imports
from ._process_common import arg_split as py_arg_split
from ._process_common import process_handler, read_no_interrupt

try:
    from ctypes.wintypes import LPCWSTR, HLOCAL
except ImportError:
    LPCWSTR = None
    HLOCAL = None


class AvoidUNCPath:
    """A context manager to protect command execution from UNC paths.

    In the Win32 API, commands can't be invoked with the cwd being a UNC path.
    This context manager temporarily changes directory to the 'C:' drive on
    entering, and restores the original working directory on exit.

    The context manager returns the starting working directory *if* it made a
    change and None otherwise, so that users can apply the necessary adjustment
    to their system calls in the event of a change.

    .. todo:: `pathlib.PurePath` objects can handle UNC paths.

    Examples
    --------
    ::

        cmd = 'dir'
        with AvoidUNCPath() as path:
            if path is not None:
                cmd = '"pushd %s &&"%s' % (path, cmd)
            os.system(cmd)
    """

    def __enter__(self):
        self.path = os.getcwd()
        self.is_unc_path = self.path.startswith(r"\\")
        if self.is_unc_path:
            # change to c drive (as cmd.exe cannot handle UNC addresses)
            os.chdir("C:")
            return self.path
        else:
            # We return None to signal that there was no change in the working
            # directory
            return None

    def __exit__(self, exc_type, exc_value, traceback):
        if self.is_unc_path:
            os.chdir(self.path)


# -----------------------------------------------------------------------------
# Function definitions
# -----------------------------------------------------------------------------


def _find_cmd(cmd):
    """Find the full path to a .bat or .exe using the win32api module.

    .. todo:: Should check :envvar:`PATHEXT` not manually guess at it.

    """
    try:
        from win32api import SearchPath
    except ImportError:
        raise ImportError("you need to have pywin32 installed for this to work")
    else:
        PATH = os.environ["PATH"]
        extensions = [".exe", ".com", ".bat", ".py"]
        path = None
        for ext in extensions:
            try:
                path = SearchPath(PATH, cmd, ext)[0]
            except BaseException:
                pass
        if path is None:
            raise OSError("command %r not found" % cmd)
        else:
            return path


def _system_body(p):
    """Callback for _system."""
    enc = sys.getfilesystemencoding()
    for line in read_no_interrupt(p.stdout).splitlines():
        line = line.decode(enc, "replace")
        print(line, file=sys.stdout)
    for line in read_no_interrupt(p.stderr).splitlines():
        line = line.decode(enc, "replace")
        print(line, file=sys.stderr)

    # Wait to finish for returncode
    return p.wait()


try:
    CommandLineToArgvW = ctypes.windll.shell32.CommandLineToArgvW
    CommandLineToArgvW.arg_types = [LPCWSTR, POINTER(c_int)]
    CommandLineToArgvW.restype = POINTER(LPCWSTR)
    LocalFree = ctypes.windll.kernel32.LocalFree
    LocalFree.res_type = HLOCAL
    LocalFree.arg_types = [HLOCAL]

    def arg_split(commandline, posix=False, strict=True):
        """Split a command line's arguments in a shell-like manner.

        This is a special version for windows that use a ctypes call to CommandLineToArgvW
        to do the argv splitting. The posix parameter is ignored.

        If strict=False, process_common.arg_split(...strict=False) is used instead.
        """
        # CommandLineToArgvW returns path to executable if called with empty
        # string.
        if commandline.strip() == "":
            return []
        if not strict:
            # not really a cl-arg, fallback on _process_common
            return py_arg_split(commandline, posix=posix, strict=strict)
        argvn = c_int()
        result_pointer = CommandLineToArgvW(commandline.lstrip(), ctypes.byref(argvn))
        result_array_type = LPCWSTR * argvn.value
        result = [
            arg
            for arg in result_array_type.from_address(
                ctypes.addressof(result_pointer.contents)
            )
        ]
        retval = LocalFree(result_pointer)
        return result


except AttributeError:
    arg_split = py_arg_split


def check_pid(pid):
    """Checks the PID of a process.

    Parameters
    ----------
    pid to check

    Returns
    -------
    OpenProcess returns 0 if no such process (of ours) exists.
    positive int otherwise

    Notes
    -----
    Uses ctypes. Added in a check that the attr exists so an accidental linux
    import doesn't throw us off.
    """
    if getattr(ctypes, "windll", None):
        return bool(ctypes.windll.kernel32.OpenProcess(1, 0, pid))
