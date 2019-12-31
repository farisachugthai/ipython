"""Editor hooks for common editors that work well with IPython.

They should honor the line number argument, at least.

Notes
-------

In this module, the functions for different editors, I.E. komodo, kate etc.
'exe' is always the path/name of the executable.

Useful if you don't have the editor directory in your path.

"""
import functools
import os
import shlex
import subprocess
import sys

from IPython.core.error import TryNext
from IPython.core.getipython import get_ipython


def komodo(exe=u"komodo"):
    """Activestate Komodo [Edit]."""
    install_editor(exe + u" -l {line} {filename}", wait=True)


def scite(exe=u"scite"):
    """SciTE or Sc1."""
    install_editor(exe + u" {filename} -goto:{line}")


def notepadplusplus(exe=u"notepad++"):
    """Notepad++ http://notepad-plus.sourceforge.net."""
    install_editor(exe + u" -n{line} {filename}")


def jed(exe=u"jed"):
    """JED, the lightweight emacsish editor."""
    install_editor(exe + u" +{line} {filename}")


def idle(exe=u"idle"):
    """Idle, the editor bundled with python.

    Parameters
    ----------
    exe : str, None
        If none, should be pretty smart about finding the executable.

    Notes
    -----
    Well this comment is reassuring....:

        # i'm not sure if this actually works. Is this idle.py script
        # guaranteed to be executable?

    """
    if exe is None:
        import idlelib

        p = os.path.dirname(idlelib.__filename__)
        exe = os.path.join(p, "idle.py")
    install_editor(exe + u" {filename}")


def mate(exe=u"mate"):
    """TextMate, the missing editor."""
    # wait=True is not required since we're using the -w flag to mate
    install_editor(exe + u" -w -l {line} {filename}")


def emacs(exe=u"emacs"):
    """

    Parameters
    ----------
    exe :
    """
    install_editor(exe + u" +{line} {filename}")


def gnuclient(exe=u"gnuclient"):
    """

    Parameters
    ----------
    exe :
    """
    install_editor(exe + u" -nw +{line} {filename}")


def crimson_editor(exe=u"cedt.exe"):
    """

    Parameters
    ----------
    exe :
    """
    install_editor(exe + u" /L:{line} {filename}")


def kate(exe=u"kate"):
    """

    Parameters
    ----------
    exe :
    """
    install_editor(exe + u" -u -l {line} {filename}")
