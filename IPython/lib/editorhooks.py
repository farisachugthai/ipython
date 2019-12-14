"""'editor' hooks for common editors that work well with IPython.

They should honor the line number argument, at least.

Contributions are *very* welcome.

.. admonition:: The functions at the end, like emacs and past, are untested.

Notes
-------
In this module, the functions for different editors, I.E. komodo, kate etc.
'exe' is always the path/name of the executable. Useful
if you don't have the editor directory in your path.

.. todo:: Only 1 line to delete before we can get rid of the py3compat import.

"""
import functools
import os
import shlex
import subprocess
import sys

from IPython.core.getipython import get_ipython
from IPython.core.error import TryNext
from IPython.utils import py3compat


def install_editor(template, wait=False):
    """Installs the editor that is called by IPython for the `%edit` magic.

    This overrides the default editor, which is generally set by your
    :envvar:`EDITOR` environment variable. As a fallback, if `EDITOR` isn't
    set, the default editor is set to :command:`notepad` on Windows
    or :command:`vi` on Unix.

    By supplying a template string `template`, you can control how the
    editor is invoked by IPython --- (e.g. the format in which it accepts
    command line options)

    Parameters
    ----------
    template : basestring
        run_template acts as a template for how your editor is invoked by
        the shell. It should contain '{filename}', which will be replaced on
        invocation with the file name, and '{line}', $line by line number
        (or 0) to invoke the file with.
    wait : bool
        If `wait` is true, wait until the user presses enter before returning,
        to facilitate non-blocking editors that exit immediately after
        the call.

    Notes
    -----
    This used to be not commented out.:

    # not all editors support $line, so we'll leave out this check
    for substitution in ['$file', '$line']:
       if not substitution in run_template:
           raise ValueError(('run_template should contain %s'
           ' for string substitution. You supplied "%s"' % (substitution,
               run_template)))

    """

    @functools.wraps
    def call_editor(self, filename, line=0):
        """I imagine this would be really easy to refactor up and out.

        Parameters
        ----------
        self :
        filename :
        line :
        """
        if line is None:
            line = 0
        cmd = template.format(filename=shlex.quote(filename), line=line)
        print(">", cmd)
        # pipes.quote doesn't work right on Windows, but it does after
        # splitting
        # or just use shlex.quote
        if sys.platform.startswith("win"):
            cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd, shell=True)
        if proc.wait():
            raise TryNext()
        if wait:
            py3compat.input("Press Enter when done editing:")

    get_ipython().set_hook("editor", call_editor)
    get_ipython().editor = template


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


# ##########################################
# these are untested, report any problems
# ##########################################


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
