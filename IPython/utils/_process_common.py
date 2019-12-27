"""Common utilities for the various process_* implementations.

This file is only meant to be imported by the platform-specific implementations
of subprocess utilities, and it contains tools that are common to all of them.

It's used quite heavily throughout the repo though so take note of that.

For example, in :mod:`IPython.testing.tools`, 'get_output_error_code' is
required, and that kicks off the entire testing suite... So don't mess with
that.

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

import os
import shlex
import subprocess
import sys
from subprocess import getoutput  # noqa F401 replaces the old getoutput func here

# -----------------------------------------------------------------------------
# Function definitions
# -----------------------------------------------------------------------------


def read_no_interrupt(p):
    """Read from a pipe ignoring EINTR errors.

    This is necessary because when reading from pipes with GUI event loops
    running in the background, often interrupts are raised that stop the
    command from completing.
    """
    import errno

    try:
        return p.read()
    except OSError as err:
        if err.errno != errno.EINTR:
            raise


def process_handler(cmd, callback, stderr=subprocess.PIPE):
    """Open a command in a shell subprocess and execute a callback.

    This function provides common scaffolding for creating subprocess.Popen()
    calls.  It creates a Popen object and then calls the callback with it.

    WAIT WHY IS THIS POSIX ONLY

    .. versionchanged:: 7.11.0 --- I've been trying to run bash on windows for so long

    Parameters
    ----------
    cmd : str or list
        A command to be executed by the system, using :class:`subprocess.Popen`.
        If a string is passed, it will be run in the system shell. If a list is
        passed, it will be used directly as arguments.
    callback : callable
        A one-argument function that will be called with the Popen object.
    stderr : file descriptor number, optional
        By default this is set to ``subprocess.PIPE``, but you can also pass the
        value ``subprocess.STDOUT`` to force the subprocess' stderr to go into
        the same file descriptor as its stdout.  This is useful to read stdout
        and stderr combined in the order they are generated.

    Returns
    -------
    The return value of the provided callback is returned.

    Notes
    -----
    On POSIX systems run shell commands with user-preferred shell.
    Should probably clean up that shell check though.::

        shell = isinstance(cmd, 'str')

    Is a terrible check. I guess for now add it as a parameter and allow None.
    Same with executable. Damn this should probably just be a class
    with a ``run`` like method.

    """
    sys.stdout.flush()
    sys.stderr.flush()
    # On win32, close_fds can't be true when using pipes for stdin/out/err
    close_fds = sys.platform != "win32"
    # Determine if cmd should be run with system shell.
    shell = isinstance(cmd, str)
    executable = None
    if shell and "SHELL" in os.environ:
        executable = os.environ["SHELL"]
    p = subprocess.Popen(
        cmd,
        shell=shell,
        executable=executable,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=stderr,
        close_fds=close_fds,
    )

    try:
        out = callback(p)
    except KeyboardInterrupt:
        print("^C")
        sys.stdout.flush()
        sys.stderr.flush()
        out = None
    finally:
        # Make really sure that we don't leave processes behind, in case the
        # call above raises an exception
        # We start by assuming the subprocess finished (to avoid NameErrors
        # later depending on the path taken)
        if p.returncode is None:
            try:
                p.terminate()
                p.poll()
            except OSError:
                pass
        # One last try on our way out
        if p.returncode is None:
            try:
                p.kill()
            except OSError:
                pass

    return out


def getoutputerror(cmd):
    """Return (standard output, standard error) of executing cmd in a shell.

    Accepts the same arguments as os.system().

    Parameters
    ----------
    cmd : str or list
      A command to be executed in the system shell.

    Returns
    -------
    stdout : str
    stderr : str
    """
    return get_output_error_code(cmd)[:2]


def get_output_error_code(cmd):
    """Return (standard output, standard error, return code) of executing cmd
    in a shell.

    Accepts the same arguments as os.system().

    Parameters
    ----------
    cmd : str or list
      A command to be executed in the system shell.

    Returns
    -------
    stdout : str
    stderr : str
    returncode: int

    """

    out_err, p = process_handler(cmd, lambda p: (p.communicate(), p))
    if out_err is None:
        return "", "", p.returncode
    out, err = out_err
    return out, err, p.returncode


def arg_split(s, posix=False, strict=True):
    """Split a command line's arguments in a shell-like manner.

    This is a modified version of the standard library's shlex.split()
    function, but with a default of posix=False for splitting, so that quotes
    in inputs are respected.

    if strict=False, then any errors shlex.split would raise will result in the
    unparsed remainder being the last element of the list, rather than raising.
    This is because we sometimes use arg_split to parse things other than
    command-line args.

    Extract tokens, ensuring that things like leaving open quotes
    does not cause this to raise.  This is important, because we
    sometimes pass Python source through this (e.g. %timeit f(" ")),
    and it shouldn't raise an exception.

    It may be a bad idea to parse things that are not command-line args
    through this function, but we do, so let's be safe about it.

    """
    lex = shlex.shlex(s, posix=posix)
    lex.whitespace_split = True
    lex.commenters = ""  # fix for GH-1269
    tokens = []
    while True:
        try:
            tokens.append(next(lex))
        except StopIteration:
            break
        except ValueError:
            if strict:
                raise
            # couldn't parse, get remaining blob as last token
            tokens.append(lex.token)
            break

    return tokens
