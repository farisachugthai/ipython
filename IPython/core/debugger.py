# -*- coding: utf-8 -*-
"""Pdb debugger class.

Modified from the standard pdb.Pdb class to avoid including readline, so that
the command line completion of other programs which include this isn't
damaged.

The code in this file is mainly lifted out of cmd.py in Python 2.2, with minor
changes. Licensing should therefore be under the standard Python terms.  For
details on the PSF (Python Software Foundation) standard license, see:

https://docs.python.org/2/license.html

https://docs.python.org/3/license.html


Portability and Python requirements
-----------------------------------
This code should really go into `../terminal/debugger` though. People won't
be using this code in the browser.

If you import our Pdb and initialize it from a standard non-IPython
Python session, we initialize an IPython session for you.

Fair enough.

Like if the user isn't currently inside of an IPython session, then we create
one. Reasonably enough.::

    >>> from IPython.terminal.interactiveshell import TerminalInteractiveShell

There's no way that that doesn't prohibit Notebook users from using this code.

There's no way that Notebook users can utilize that, so I'd assume that this
code is basically unavailable to them.

API
----

.. data:: prompt

    The prompt the user gets in the shell.

"""
# *****************************************************************************
#       This file is licensed under the PSF license.

#       Copyright (C) 2001 Python Software Foundation, www.python.org
#       Copyright (C) 2005-2006 Fernando Perez. <fperez@colorado.edu>
# *****************************************************************************

import bdb
import functools
import inspect
import linecache
import re
import reprlib
import sys
import warnings
from bdb import BdbQuit
from pdb import Pdb

from IPython.core.error import (
    BdbQuit_excepthook,
    BdbQuit_IPython_excepthook,
    UsageError,
)
from IPython.core.excolors import exception_colors
from IPython.core.getipython import get_ipython
from IPython.utils import PyColorize, coloransi

# We have to check this directly from sys.argv, config struct not yet available
prompt = "ipdb> "

# Allow the set_trace code to operate outside of an ipython instance, even if
# it does so with some limitations.  The rest of this support is implemented in
# the Tracer constructor.
# Didn't we deprecate Tracer?


def make_arrow(pad):
    """Generate the leading arrow in front of traceback or debugger."""
    if pad >= 2:
        return "-" * (pad - 2) + "> "
    elif pad == 1:
        return ">"
    return ""


def strip_indentation(multiline_string):
    """textwrap.dedent?"""
    RGX_EXTRA_INDENT = re.compile(r"(?<=\n)\s+")
    return RGX_EXTRA_INDENT.sub("", multiline_string)


def decorate_fn_with_doc(new_fn, old_fn, additional_text=""):
    """Make new_fn have old_fn's doc string. This is particularly useful
    for the ``do_...`` commands that hook into the help system.

    Adapted from from a comp.lang.python posting
    by Duncan Booth.

    Uhhh so what the hell does this do that functools.wraps() doesn't?

    Still can't tell and it's used 3 different times in this mod.
    """

    def wrapper(*args, **kw):
        """

        Parameters
        ----------
        args :
        kw :

        Returns
        -------

        """
        return new_fn(*args, **kw)

    if old_fn.__doc__:
        wrapper.__doc__ = strip_indentation(old_fn.__doc__) + additional_text
    return wrapper


class CorePdb(Pdb):
    """Modified Pdb class, does not load readline.

    For a standalone version that uses prompt_toolkit, see
    `IPython.terminal.debugger.TerminalPdb` and
    `IPython.terminal.debugger.set_trace()`

    Comments from the constructor.:

        # Create color table: we copy the default one from the traceback
        # module and add a few attributes needed for debugging

    """

    def __init__(
        self,
        color_scheme=None,
        completekey=None,
        stdin=None,
        stdout=None,
        context=5,
        aliases=None,
        prompt="IPdb> ",
        shell=None,
        **kwargs,
    ):
        """Create a new IPython debugger.

        .. todo::
            Add shell to constructor.
            Possibly add the variable ``namespaces`` as well.
            Check the methods :meth:`do_pdef`, :meth:`do_pdoc` and etc.
            They all start out the same way like there's no need for the repitition.

        :param color_scheme: Deprecated, do not use.
        :param completekey: Passed to `pdb.Pdb`.
        :param stdin: Passed to `pdb.Pdb`.
        :param stdout: Passed to `pdb.Pdb`.
        :param context: Number of lines of source code context to show when
                        displaying stacktrace information.
        :param aliases: User defined aliases.
        :param prompt: ``$PS1``
        :param shell: IPython instance.
        :param kwargs: Passed to pdb.Pdb.
            The possibilities are python version dependent, see the python
            docs for more info.

        """
        # Parent constructor:
        try:
            self.context = int(context)
            if self.context <= 0:
                raise ValueError("Context must be a positive integer")
        except (TypeError, ValueError):
            raise ValueError("Context must be a positive integer")

        # `kwargs` ensures full compatibility with stdlib's `pdb.Pdb`.
        super().__init__(self, completekey, stdin, stdout, **kwargs)

        # IPython changes...
        self.shell = shell or get_ipython()

        if self.shell is None:
            save_main = sys.modules["__main__"]
            # No IPython instance running, we must create one
            from IPython.terminal.interactiveshell import TerminalInteractiveShell

            self.shell = TerminalInteractiveShell.instance()
            # needed by any code which calls __import__("__main__") after
            # the debugger was entered. See also #9941.
            sys.modules["__main__"] = save_main

        self.aliases = aliases or {}

        # Set the prompt - the default prompt is '(Pdb)'
        self.prompt = prompt

    def debug_colors(self):
        """Ah the plethora of meaning here.

        Both this method and set_colors need some heavy debugging.

        The modules they import from are the problem children of this repo.
        """
        self.color_scheme_table = exception_colors()

        # shorthands
        C = coloransi.TermColors
        cst = self.color_scheme_table

        cst["NoColor"].colors.prompt = C.NoColor
        cst["NoColor"].colors.breakpoint_enabled = C.NoColor
        cst["NoColor"].colors.breakpoint_disabled = C.NoColor

        cst["Linux"].colors.prompt = C.Green
        cst["Linux"].colors.breakpoint_enabled = C.LightRed
        cst["Linux"].colors.breakpoint_disabled = C.Red

        cst["LightBG"].colors.prompt = C.Blue
        cst["LightBG"].colors.breakpoint_enabled = C.LightRed
        cst["LightBG"].colors.breakpoint_disabled = C.Red

        cst["Neutral"].colors.prompt = C.Blue
        cst["Neutral"].colors.breakpoint_enabled = C.LightRed
        cst["Neutral"].colors.breakpoint_disabled = C.Red

        # Add a python parser so we can syntax highlight source while
        # debugging.
        self.parser = PyColorize.Parser(style=color_scheme)
        self.set_colors(color_scheme)

    def set_colors(self, scheme):
        """Shorthand access to the color table scheme selector method."""
        self.color_scheme_table.set_active_scheme(scheme)
        self.parser.style = scheme

    def interaction(self, frame, traceback):
        """

        Parameters
        ----------
        frame :
        traceback :
        """
        try:
            Pdb.interaction(self, frame, traceback)
        except KeyboardInterrupt:
            self.stdout.write("\n" + self.shell.get_exception_only())

    def new_do_up(self, arg):
        """So this calls the superclasses method directly. Should we turn into a super call? How do we handle this?"""
        Pdb.do_up(self, arg)

    do_u = do_up = decorate_fn_with_doc(new_do_up, Pdb.do_up)

    def new_do_down(self, arg):
        """

        Parameters
        ----------
        arg :
        """
        Pdb.do_down(self, arg)

    do_d = do_down = decorate_fn_with_doc(new_do_down, Pdb.do_down)

    def new_do_frame(self, arg):
        """

        Parameters
        ----------
        arg :
        """
        Pdb.do_frame(self, arg)

    def new_do_quit(self, arg):
        """

        Parameters
        ----------
        arg :

        Returns
        -------

        """
        if hasattr(self, "old_all_completions"):
            self.shell.Completer.all_completions = self.old_all_completions

        return Pdb.do_quit(self, arg)

    do_q = do_quit = decorate_fn_with_doc(new_do_quit, Pdb.do_quit)

    def new_do_restart(self, arg):
        """Restart command. In the context of ipython this is exactly the same
        thing as 'quit'."""
        self.msg("Restart doesn't make sense here. Using 'quit' instead.")
        return self.do_quit(arg)

    def print_stack_trace(self, context=None):
        """

        Parameters
        ----------
        context :
        """
        if context is None:
            context = self.context
        try:
            context = int(context)
            if context <= 0:
                raise ValueError("Context must be a positive integer")
        except (TypeError, ValueError):
            raise ValueError("Context must be a positive integer")
        try:
            for frame_lineno in self.stack:
                self.print_stack_entry(frame_lineno, context=context)
        except KeyboardInterrupt:
            pass

    def print_stack_entry(self, frame_lineno, prompt_prefix="\n-> ", context=None):
        """

        Parameters
        ----------
        frame_lineno :
        prompt_prefix :
        context :
        """
        if context is None:
            context = self.context
        try:
            context = int(context)
            if context <= 0:
                raise ValueError("Context must be a positive integer")
        except (TypeError, ValueError):
            raise ValueError("Context must be a positive integer")
        print(self.format_stack_entry(frame_lineno, "", context), file=self.stdout)

        # vds: >>
        frame, lineno = frame_lineno
        filename = frame.f_code.co_filename
        self.shell.hooks.synchronize_with_editor(filename, lineno, 0)
        # vds: <<

    def format_stack_entry(self, frame_lineno, lprefix=": ", context=None):
        """

        Parameters
        ----------
        frame_lineno :
        lprefix :
        context :

        Returns
        -------

        """
        try:
            which_frame = abs(self.context)
        except (TypeError, ValueError):
            raise UsageError("context must be a positive integer.")

        ret = []

        Colors = self.color_scheme_table.active_colors
        ColorsNormal = Colors.Normal
        tpl_link = "%s%%s%s" % (Colors.filenameEm, ColorsNormal)
        tpl_call = "%s%%s%s%%s%s" % (Colors.vName, Colors.valEm, ColorsNormal)
        tpl_line = "%%s%s%%s %s%%s" % (Colors.lineno, ColorsNormal)
        tpl_line_em = "%%s%s%%s %s%%s%s" % (Colors.linenoEm, Colors.line, ColorsNormal)

        frame, lineno = frame_lineno

        return_value = ""
        if "__return__" in frame.f_locals:
            rv = frame.f_locals["__return__"]
            # return_value += '->'
            return_value += reprlib.repr(rv) + "\n"
        ret.append(return_value)

        # s = filename + '(' + `lineno` + ')'
        filename = self.canonic(frame.f_code.co_filename)
        link = tpl_link % filename

        if frame.f_code.co_name:
            func = frame.f_code.co_name
        else:
            func = "<lambda>"

        call = ""
        if func != "?":
            if "__args__" in frame.f_locals:
                args = reprlib.repr(frame.f_locals["__args__"])
            else:
                args = "()"
            call = tpl_call % (func, args)

        # The level info should be generated in the same format pdb uses, to
        # avoid breaking the pdbtrack functionality of python-mode in *emacs.
        if frame is self.curframe:
            ret.append("> ")
        else:
            ret.append("  ")
        ret.append("%s(%s)%s\n" % (link, lineno, call))

        start = lineno - 1 - context // 2
        lines = linecache.getlines(filename)
        start = min(start, len(lines) - context)
        start = max(start, 0)
        lines = lines[start : start + context]

        for i, line in enumerate(lines):
            show_arrow = start + 1 + i == lineno
            linetpl = (frame is self.curframe or show_arrow) and tpl_line_em or tpl_line
            ret.append(
                self.__format_line(
                    linetpl, filename, start + 1 + i, line, arrow=show_arrow
                )
            )
        return "".join(ret)

    def __format_line(self, tpl_line, filename, lineno, line, arrow=False):
        bp_mark = ""
        bp_mark_color = ""

        new_line, err = self.parser.format2(line, "str")
        if not err:
            line = new_line

        bp = None
        if lineno in self.get_file_breaks(filename):
            bps = self.get_breaks(filename, lineno)
            bp = bps[-1]

        if bp:
            Colors = self.color_scheme_table.active_colors
            bp_mark = str(bp.number)
            bp_mark_color = Colors.breakpoint_enabled
            if not bp.enabled:
                bp_mark_color = Colors.breakpoint_disabled

        numbers_width = 7
        if arrow:
            # This is the line with the error
            pad = numbers_width - len(str(lineno)) - len(bp_mark)
            num = "%s%s" % (make_arrow(pad), str(lineno))
        else:
            num = "%*s" % (numbers_width - len(bp_mark), str(lineno))

        return tpl_line % (bp_mark_color + bp_mark, num, line)

    def print_list_lines(self, filename, first, last):
        """The printing. (as opposed to the parsing part of a 'list' command."""
        try:
            Colors = self.color_scheme_table.active_colors
            ColorsNormal = Colors.Normal
            tpl_line = "%%s%s%%s %s%%s" % (Colors.lineno, ColorsNormal)
            tpl_line_em = "%%s%s%%s %s%%s%s" % (
                Colors.linenoEm,
                Colors.line,
                ColorsNormal,
            )
            src = []
            if filename == "<string>" and hasattr(self, "_exec_filename"):
                filename = self._exec_filename

            for lineno in range(first, last + 1):
                line = linecache.getline(filename, lineno)
                if not line:
                    break

                if lineno == self.curframe.f_lineno:
                    line = self.__format_line(
                        tpl_line_em, filename, lineno, line, arrow=True
                    )
                else:
                    line = self.__format_line(
                        tpl_line, filename, lineno, line, arrow=False
                    )

                src.append(line)
                self.lineno = lineno

            print("".join(src), file=self.stdout)

        except KeyboardInterrupt:
            # pass well at least notify them.
            print("Interrupted!")

    def do_list(self, arg):
        """Print lines of code from the current stack frame.
        """
        self.lastcmd = "list"
        last = None
        if arg:
            try:
                x = eval(arg, {}, {})
                if type(x) == type(()):
                    first, last = x
                    first = int(first)
                    last = int(last)
                    if last < first:
                        # Assume it's a count
                        last += first
                else:
                    first = max(1, int(x) - 5)
            except BaseException:
                print("*** Error in argument:", repr(arg), file=self.stdout)
                return
        elif self.lineno is None:
            first = max(1, self.curframe.f_lineno - 5)
        else:
            first = self.lineno + 1
        if last is None:
            last = first + 10
        self.print_list_lines(self.curframe.f_code.co_filename, first, last)

        # vds: >>
        lineno = first
        filename = self.curframe.f_code.co_filename
        self.shell.hooks.synchronize_with_editor(filename, lineno, 0)
        # vds: <<

    do_l = do_list

    def getsourcelines(self, obj):
        """

        Parameters
        ----------
        obj :

        Returns
        -------

        """
        lines, lineno = inspect.findsource(obj)
        if inspect.isframe(obj) and obj.f_globals is obj.f_locals:
            # must be a module frame: do not try to cut a block out of it
            return lines, 1
        elif inspect.ismodule(obj):
            return lines, 1
        return inspect.getblock(lines[lineno:]), lineno + 1

    def do_longlist(self, arg):
        """Print lines of code from the current stack frame.

        Shows more lines than 'list' does.
        """
        self.lastcmd = "longlist"
        try:
            lines, lineno = self.getsourcelines(self.curframe)
        except OSError as err:
            self.error(err)
            return
        last = lineno + len(lines)
        self.print_list_lines(self.curframe.f_code.co_filename, lineno, last)

    do_ll = do_longlist

    def do_debug(self, arg):
        """debug code
        Enter a recursive debugger that steps through the code
        argument (which is an arbitrary expression or statement to be
        executed in the current environment).
        """
        sys.settrace(None)
        globals = self.curframe.f_globals
        locals = self.curframe_locals
        p = self.__class__(
            completekey=self.completekey, stdin=self.stdin, stdout=self.stdout
        )
        p.use_rawinput = self.use_rawinput
        p.prompt = "(%s) " % self.prompt.strip()
        self.message("ENTERING RECURSIVE DEBUGGER")
        sys.call_tracing(p.run, (arg, globals, locals))
        self.message("LEAVING RECURSIVE DEBUGGER")
        sys.settrace(self.trace_dispatch)
        self.lastcmd = p.lastcmd

    def do_pdef(self, arg):
        """Print the call signature for any callable object.

        The debugger interface to `%pdef`.
        """
        namespaces = [
            ("Locals", self.curframe.f_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("pdef")(arg, namespaces=namespaces)

    def do_pdoc(self, arg):
        """Print the docstring for an object.

        The debugger interface to `%pdoc.`
        """
        namespaces = [
            ("Locals", self.curframe.f_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("pdoc")(arg, namespaces=namespaces)

    def do_pfile(self, arg):
        """Print (or run through pager) the file where an object is defined.

        The debugger interface to %pfile.
        """
        namespaces = [
            ("Locals", self.curframe.f_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("pfile")(arg, namespaces=namespaces)

    def do_pinfo(self, arg):
        """Provide detailed information about an object.

        The debugger interface to %pinfo, i.e., obj?."""
        namespaces = [
            ("Locals", self.curframe.f_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("pinfo")(arg, namespaces=namespaces)

    def do_pinfo2(self, arg):
        """Provide extra detailed information about an object.

        The debugger interface to %pinfo2, i.e., obj??."""
        namespaces = [
            ("Locals", self.curframe.f_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("pinfo2")(arg, namespaces=namespaces)

    def do_psource(self, arg):
        """Print (or run through pager) the source code for an object."""
        namespaces = [
            ("Locals", self.curframe.f_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("psource")(arg, namespaces=namespaces)

    def do_where(self, arg):
        """w(here)
        Print a stack trace, with the most recent frame at the bottom.
        An arrow indicates the "current frame", which determines the
        context of most commands. 'bt' is an alias for this command.

        Take a number as argument as an (optional) number of context line to
        print"""
        if arg:
            context = int(arg)
            self.print_stack_trace(context)
        else:
            self.print_stack_trace()

    do_w = do_where


# enough modules import this thibking its jere so we should
Pdb = CorePdb


def set_trace(frame=None):
    """Start debugging from `frame`.

    If frame is not specified, debugging starts from caller's frame.

    The function is simply this:

    Examples
    --------
    >>> Pdb().set_trace(frame or sys._getframe().f_back)

    """
    CorePdb().set_trace(frame or sys._getframe().f_back)
