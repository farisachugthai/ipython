"""Logger class for IPython's logging facilities.

Based on PEP 282.
"""

# *****************************************************************************
#       Copyright (C) 2001 Janko Hauser <jhauser@zscout.de> and
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************

# ****************************************************************************
# Modules and globals

# Python standard modules
import codecs
import glob
import io

# How does this not import logging?
import logging
import os
from pathlib import Path
import time

from traitlets.config import Configurable, Bool


class BracketFormatter(logging.Formatter):
    """Formatter with additional `highlevel` record

    This field is empty if log level is less than highlevel_limit,
    otherwise it is formatted with self.highlevel_format.

    Useful for adding 'WARNING' to warning messages,
    without adding 'INFO' to info, etc.
    """

    def __init__(self, highlevel_limit=None, highlevel_format=None, *args, **kwargs):
        """Slipped my mind that using ``{}`` in log messages is non-standard....

        Let's override that.
        """
        self.highlevel_limit = logging.WARN or highlevel_limit
        self.highlevel_format = " %(module)s | %(levelname)s |" or highlevel_format
        super().__init__(self, *args, **kwargs)

    def format(self, record=None):
        if not record:
            return
        if record.levelno >= self.highlevel_limit:
            record.highlevel = self.highlevel_format % record.__dict__
        else:
            record.highlevel = ""
        return super().format(record)


# ****************************************************************************
# FIXME: This class isn't a mixin anymore, but it still needs attributes from
# ipython and does input cache management.  Finish cleanup later...


class Logger:
    """A Logfile class with different policies for file creation"""

    def __init__(
        self, home_dir=None, logfname="Logger.log", loghead="", logmode="over"
    ):

        # this is the full ipython instance, we need some attributes from it
        # which won't exist until later. What a mess, clean up later...
        self.home_dir = home_dir or Path.home().__fspath__()

        self.logfname = logfname
        self.loghead = loghead
        self.logmode = logmode
        self.logfile = None

        # Whether to log raw or processed input
        self.log_raw_input = False

        # whether to also log output
        self.log_output = False

        # whether to put timestamps before each log entry
        self.timestamp = False

        # activity control flags
        self.log_active = False

    def _set_mode(self, mode):
        """'logmode' is a validated property."""
        if mode not in ["append", "backup", "global", "over", "rotate"]:
            raise ValueError("invalid log mode %s given" % mode)
        self._logmode = mode

    def _get_mode(self):
        return self._logmode

    logmode = property(_get_mode, _set_mode)

    def logstart(
        self,
        logfname=None,
        loghead=None,
        logmode=None,
        log_output=False,
        timestamp=False,
        log_raw_input=False,
    ):
        """Generate a new log-file with a default header.

        Raises
        ------
        :exc:`RuntimeError`
            If the log has already been started.
        """

        if self.logfile is not None:
            raise RuntimeError("Log file is already active: %s" % self.logfname)

        # The parameters can override constructor defaults
        if logfname is not None:
            self.logfname = logfname
        if loghead is not None:
            self.loghead = loghead
        if logmode is not None:
            self.logmode = logmode

        # Parameters not part of the constructor
        self.timestamp = timestamp
        self.log_output = log_output
        self.log_raw_input = log_raw_input

        # init depending on the log mode requested
        isfile = os.path.isfile
        logmode = self.logmode

        if logmode == "append":
            self.logfile = codecs.open(self.logfname, "a", encoding="utf-8")

        elif logmode == "backup":
            if isfile(self.logfname):
                backup_logname = self.logfname + "~"
                # Manually remove any old backup, since os.rename may fail
                # under Windows.
                if isfile(backup_logname):
                    os.remove(backup_logname)
                os.rename(self.logfname, backup_logname)
            self.logfile = codecs.open(self.logfname, "w", encoding="utf-8")

        elif logmode == "global":
            self.logfname = os.path.join(self.home_dir, self.logfname)
            self.logfile = codecs.open(self.logfname, "a", encoding="utf-8")

        elif logmode == "over":
            if isfile(self.logfname):
                os.remove(self.logfname)
            self.logfile = codecs.open(self.logfname, "w", encoding="utf-8")

        elif logmode == "rotate":
            if isfile(self.logfname):
                if isfile(self.logfname + ".001~"):
                    old = sorted(glob.glob(self.logfname + ".*~"))
                    old.reverse()
                    for f in old:
                        root, ext = os.path.splitext(f)
                        num = int(ext[1:-1]) + 1
                        os.rename(f, root + "." + repr(num).zfill(3) + "~")
                os.rename(self.logfname, self.logfname + ".001~")
            self.logfile = codecs.open(self.logfname, "w", encoding="utf-8")

        if logmode != "append":
            self.logfile.write(self.loghead)

        self.logfile.flush()
        self.log_active = True

    def switch_log(self, val):
        """Switch logging on/off. val should be ONLY a boolean."""

        if val not in [False, True, 0, 1]:
            raise ValueError(
                "Call switch_log ONLY with a boolean argument, " "not with: %s" % val
            )

        label = {0: "OFF", 1: "ON", False: "OFF", True: "ON"}

        if self.logfile is None:
            print(
                """
Logging hasn't been started yet (use logstart for that).

%logon/%logoff are for temporarily starting and stopping logging for a logfile
which already exists. But you must first start the logging process with
%logstart (optionally giving a logfile name)."""
            )

        else:
            if self.log_active == val:
                print("Logging is already", label[val])
            else:
                print("Switching logging", label[val])
                self.log_active = not self.log_active
                self.log_active_out = self.log_active

    def logstate(self):
        """Print a status message about the logger."""
        if self.logfile is None:
            print("Logging has not been activated.")
        else:
            state = self.log_active and "active" or "temporarily suspended"
            print("Filename       :", self.logfname)
            print("Mode           :", self.logmode)
            print("Output logging :", self.log_output)
            print("Raw input log  :", self.log_raw_input)
            print("Timestamping   :", self.timestamp)
            print("State          :", state)

    def log(self, line_mod, line_ori):
        """Write the sources to a log.

        Inputs:

        - line_mod: possibly modified input, such as the transformations made
          by input prefilters or input handlers of various kinds. This should
          always be valid Python.

        - line_ori: unmodified input line from the user. This is not
          necessarily valid Python.
        """

        # Write the log line, but decide which one according to the
        # log_raw_input flag, set when the log is started.
        if self.log_raw_input:
            self.log_write(line_ori)
        else:
            self.log_write(line_mod)

    def log_write(self, data, kind="input"):
        """Write data to the log file, if active"""

        # print 'data: %r' % data # dbg
        if self.log_active and data:
            write = self.logfile.write
            if kind == "input":
                if self.timestamp:
                    write(time.strftime("# %a, %d %b %Y %H:%M:%S\n", time.localtime()))
                write(data)
            elif kind == "output" and self.log_output:
                odata = "\n".join(["#[Out]# %s" % s for s in data.splitlines()])
                write("%s\n" % odata)
            self.logfile.flush()

    def logstop(self):
        """Fully stop logging and close log file.

        In order to start logging again, a new logstart() call needs to be
        made, possibly (though not necessarily) with a new filename, mode and
        other options."""

        if self.logfile is not None:
            self.logfile.close()
            self.logfile = None
        else:
            print("Logging hadn't been started.")
        self.log_active = False

    # For backwards compatibility, in case anyone was using this.
    close_log = logstop


class LoggerManager(Configurable):
    """Let's give cleanup a shot.

    Attributes
    ----------
    logfile : str (os.Pathlike)
        Be careful to not set this immediately. We set it with
        :meth:`logstart` and it will raise an error if set early.
    log_raw_input : bool
        Whether to log raw or processed input.
    log_output : bool
        Whether to also log output.
    timestamp : bool
        Whether to put timestamps before each log entry.
    log_active : bool
        activity control flags
    home : str
        Not in init because it doesn't make any sense to override where
        your home directory is.

    """

    log_raw_input = Bool(False, help="Whether to log raw or processed input").tag(
        config=True
    )
    log_output = Bool(False, help="Whether to also log output.").tag(config=True)
    timestamp = Bool(
        False, help="Whether to put timestamps before each log entry."
    ).tag(config=True)
    log_active = Bool(False, help="activity control flags").tag(config=True)

    def __init__(
        self, logfname="Logger.log", loghead=None, logmode=None, *args, **kwargs
    ):
        """New LoggerManager.

        Parameters
        ----------
        logfname : str
            Is set to the attribute 'logfile' in method :meth:`logstart`.

        """
        super().__init__(*args, **kwargs)
        self.home = Path.home().__fspath__()
        self.logfname = logfname
        self.loghead = loghead
        self.logmode = logmode
        self.log_raw_input = log_raw_input
        self.log_output = log_output
        self.timestamp = timestamp
        self.log_active = log_active

    @property
    def _mode(self):
        return self._logmode

    @_mode.setter
    def _set_mode(self, mode):
        """'logmode' is a validated property."""
        if mode not in ["append", "backup", "global", "over", "rotate"]:
            raise ValueError("invalid log mode %s given" % mode)
        self._logmode = mode

    def append(self):
        """Called when logmode is set to append."""
        return codecs.open(self.logfname, "a", encoding="utf-8")

    def backup(self, backupext="~"):
        """Added a backupext parameter so that can be changed.

        Also changed the logfile to be open in append mode so we don't have
        to worry about whether we have more.
        """
        if isfile(self.logfname):
            backup_logname = self.logfname + backupext
            os.rename(self.logfname, backup_logname)
        return codecs.open(self.logfname, "a", encoding="utf-8")

    def global_mode(self):
        self.logfname = os.path.join(self.home_dir, self.logfname)
        return codecs.open(self.logfname, "a", encoding="utf-8")

    def over(self):
        return codecs.open(self.logfname, "w", encoding="utf-8")

    @property
    def output_file(self):
        return self.logfile

    @output_file.setter
    def set_output_file(self):
        if logmode == "append":
            self.logfile = self.append()

        elif logmode == "backup":
            self.logfile = self.backup()

        elif logmode == "global":  # can't name a method global
            self.logfile = self.global_mode()

        elif logmode == "over":
            self.logfile = self.over()

        elif logmode == "rotate":
            if isfile(self.logfname):
                if isfile(self.logfname + ".001~"):
                    old = sorted(glob.glob(self.logfname + ".*~"))
                    old.reverse()
                    for f in old:
                        root, ext = os.path.splitext(f)
                        num = int(ext[1:-1]) + 1
                        os.rename(f, root + "." + repr(num).zfill(3) + "~")
                os.rename(self.logfname, self.logfname + ".001~")
            self.logfile = codecs.open(self.logfname, "w", encoding="utf-8")

        return self.logfile

    def logstart(self):
        """Generate a new log-file with a default header.

        Parameters
        ----------
        Raises
        ------
        :exc:`RuntimeError`
            If the log has already been started via 'logfile' being set.

        """
        if self.logfile is not None:
            raise RuntimeError("Log file is already active: %s" % self.logfname)
        self.logfile = self.set_outputfile()

        if logmode != "append":
            self.logfile.write(self.loghead)
        self.logfile.flush()
        self.log_active = True
