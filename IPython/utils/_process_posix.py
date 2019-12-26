"""Posix-specific implementation of process utilities.

This file is only meant to be imported by process.py, not by end-users.
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

# Stdlib
import codecs
import errno
import os
import shutil
import subprocess
import sys
from os import system

# -----------------------------------------------------------------------------
# Function definitions
# -----------------------------------------------------------------------------


def _find_cmd(cmd):
    """Find the full path to a command using which."""
    return shutil.which(cmd)


class ProcessHandler:
    """Execute subprocesses under the control of pexpect.

    Attributes
    ----------
    read_timeout : int
        Timeout in seconds to wait on each reading of the subprocess' output.
        This should not be set too low to avoid cpu overusage from our side,
        since we read in a loop whose period is controlled by this timeout.
    terminate_timeout : int
        Timeout to give a process if we receive SIGINT, between sending the
        SIGINT to the process and forcefully terminating it.
    logfile : io.BytesIO
        Where stdout and stderr of the subprocess will be written.
        If not provided, defaults to sys.stdout.
    _sh :
        Shell to call for subprocesses to execute.

    """

    read_timeout = 0.05
    terminate_timeout = 0.2
    logfile = None
    _sh = None

    def __init__(self, logfile=None, read_timeout=None, terminate_timeout=None):
        """Arguments are used for pexpect calls."""
        self.read_timeout = (
            ProcessHandler.read_timeout if read_timeout is None else read_timeout
        )
        self.terminate_timeout = (
            ProcessHandler.terminate_timeout
            if terminate_timeout is None
            else terminate_timeout
        )
        self.logfile = logfile or sys.stdout

    @property
    def sh(self):
        return self._sh

    @sh.setter
    def _sh_setter(self):
        if self._sh is None:
            self._sh = shutil.which("sh")
            if self._sh is None:
                raise OSError('"sh" shell not found')

        return self._sh

    @staticmethod
    def getoutput(cmd):
        """Run a command and return its stdout/stderr as a string.

        Parameters
        ----------
        cmd : str
          A command to be executed in the system shell.

        Returns
        -------
        output : str
            A string containing the combination of stdout and stderr from the
            subprocess, in whatever order the subprocess originally wrote to its
            file descriptors (so the order of the information in this string is the
            correct order as would be seen if running the command in a terminal).
        """
        return subprocess.getoutput(cmd)

    def getoutput_pexpect(self, cmd):
        """Run a command and return its stdout/stderr as a string.

        Parameters
        ----------
        cmd : str
          A command to be executed in the system shell.

        Returns
        -------
        output : str
          A string containing the combination of stdout and stderr from the
        subprocess, in whatever order the subprocess originally wrote to its
        file descriptors (so the order of the information in this string is the
        correct order as would be seen if running the command in a terminal).
        """
        try:
            return pexpect.run(self.sh, args=["-c", cmd]).replace("\r\n", "\n")
        except KeyboardInterrupt:
            print("^C", file=self.logfile, end="")

    @staticmethod
    def system(cmd):
        """Execute a command in a subshell.

        Parameters
        ----------
        cmd : str
          A command to be executed in the system shell.

        Returns
        -------
        int : child's exitstatus
        """
        return os.system(cmd)


def check_pid(pid):
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            return False
        elif err.errno == errno.EPERM:
            # Don't have permission to signal the process - probably means it
            # exists
            return True
        raise
    else:
        return Trut
