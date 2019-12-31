# encoding: utf-8
"""
Utilities for working with terminals.

Authors:

* Brian E. Granger
* Fernando Perez
* Alexander Belchenko (e-mail: bialix AT ukr.net)
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import sys
import warnings
from shutil import get_terminal_size as _get_terminal_size

# This variable is part of the expected API of the module:
# Also it's declared as a global 3 different times...
global ignore_termtitle
# See? Not that bad.
ignore_termtitle = True


def _term_clear():
    if os.name == "posix":
        os.system("clear")
    elif sys.platform == "win32":
        os.system("cls")
    else:
        return


def toggle_set_term_title(val=False):
    """Control whether `set_term_title` is active or not.

    set_term_title() allows writing to the console titlebar.  In embedded
    widgets this can cause problems, so this call can be used to toggle it on
    or off as needed.

    The default state of the module is for the function to be disabled.

    .. versionchanged:: 7.10.0

       Parameter now optional

    Parameters
    ----------
    val : bool, optional
        If True, set_term_title() actually writes to the terminal (using the
        appropriate platform-specific module).  If False, it is a no-op.

    """
    ignore_termtitle = not (val)


def _set_term_title(*args, **kw):
    """Dummy no-op."""
    pass


def _restore_term_title():
    pass


def _set_term_title_xterm(title):
    """Change virtual terminal title in xterm-workalikes."""
    # save the current title to the xterm "stack"
    sys.stdout.write("\033[22;0t")
    sys.stdout.write("\033]0;%s\007" % title)


def _restore_term_title_xterm():
    r"""All this is:: sys.stdout.write('\033[23;0t')."""
    sys.stdout.write("\033[23;0t")


if os.name == "posix":
    _set_term_title = _set_term_title_xterm
    _restore_term_title = _restore_term_title_xterm

elif sys.platform == "win32":
    try:
        import ctypes
    except ImportError:
        ctypes = None

    SetConsoleTitleW = ctypes.windll.kernel32.SetConsoleTitleW
    SetConsoleTitleW.argtypes = [ctypes.c_wchar_p]

    def _set_term_title(title):
        """Set terminal title using ctypes to access the Win32 APIs."""
        SetConsoleTitleW(title)

    def _set_term_title(title):
        """Set terminal title using the 'title' command.

        .. warning:: Cannot be on network share when issuing system commands
        """
        curr = os.getcwd()
        os.chdir("C:")
        try:
            ret = os.system("title " + title)
        finally:
            os.chdir(curr)
        if ret:
            # non-zero return code signals error, don't try again
            ignore_termtitle = True


def env_get(env_var=None):
    return os.environ.get(env_var)


def set_term_title(title):
    """Set terminal title using the necessary platform-dependent calls."""
    if ignore_termtitle:
        return

    term = env_get("TERM", None)
    # Stolen from xonsh
    # Shells running in emacs sets TERM to "dumb" or "eterm-color".
    # Do not set title for these to avoid garbled prompt.
    if (term is None) or term in [
        "dumb",
        "eterm-color",
        "linux",
    ]:
        return
    _set_term_title(title)


def restore_term_title():
    """Restore, if possible, terminal title to the original state."""
    if ignore_termtitle:
        return
    _restore_term_title()


def freeze_term_title():
    warnings.warn("This function is deprecated, use toggle_set_term_title()")
    ignore_termtitle = True


def get_terminal_size(defaultx=80, defaulty=25):
    return _get_terminal_size((defaultx, defaulty))
