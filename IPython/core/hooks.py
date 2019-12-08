"""Hooks for IPython.

In Python, it is possible to overwrite any method of any object if you really
want to.  But IPython exposes a few 'hooks', methods which are *designed* to
be overwritten by users for customization purposes.  This module defines the
default versions of all such hooks, which get used by IPython if not
overridden by the user.

Hooks are simple functions, but they should be declared with ``self`` as their
first argument, because when activated they are registered into IPython as
instance methods. The self argument will be the IPython running instance
itself, so hooks have full access to the entire IPython object.

If you wish to define a new hook and activate it, you can make an
:ref:`extension <extensions>`
or a :ref:`startup script <startup_files>`.

For example, you could use a startup file like this:

Isn't it kinda confusing to say use a startup file when we invoke the
load_ipython_extension function below?

Why not just say.

For example, you could write an extension like this::

    import os
    def calljed(self,filename, linenum):
        "My editor hook calls the jed editor directly."
        print "Calling my own editor, jed ..."
        if os.system('jed +%d %s' % (linenum,filename)) != 0:
            raise TryNext()

    def load_ipython_extension(ip):
        ip.set_hook('editor', calljed)


Wait but if jed get's called successfully but crashes won't os.system return
!=0? Isn't it a better idea to do :func:`shutil.which` and make THAT the hook.
Like I mean.::

    from IPython import get_ipython

    def checkjed(self, filename, lnum):
        if shutil.which('jed'):

            arbitrary_mapping = {'shell': self,
            'filename': filename,
            'line_number': lnum}

            return calljed(arbitrary_mapping)
        else:
            raise TryNext()

    def calljed(**kwargs):
        # Because i have no idea what jed is.
        raise NotImplementedError

    if __name__ == "__main__":
        shell = get_ipython()
        if shell:
            checkjed(shell, filename=sys.argv[1:], lnum=0)

Generally.

"""
# *****************************************************************************
#       Copyright (C) 2005 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************
import shlex
import subprocess
import sys

from IPython.core.error import TryNext

# List here all the default hooks.  For now it's just the editor functions
# but over time we'll move here all the public API for user-accessible things.

__all__ = [
    "editor",
    "synchronize_with_editor",
    "shutdown_hook",
    "late_startup_hook",
    "show_in_pager",
    "pre_prompt_hook",
    "pre_run_code_hook",
    "clipboard_get",
]

deprecated = {
    "pre_run_code_hook": "a callback for the 'pre_execute' or 'pre_run_cell' event",
    "late_startup_hook": "a callback for the 'shell_initialized' event",
    "shutdown_hook": "the atexit module",
}


def editor(self, filename, linenum=None, wait=True):
    """Open the default editor at the given filename and linenumber.

    IPython configures a default editor at startup by reading
    :envvar:`EDITOR` from the environment, and falling back on
    :command:`vi` on Unix-like systems or Notepad on Windows.

    This is IPython's default editor hook, you can use it as an example to
    write your own modified one.

    Examples
    --------
    To set your own editor function as the new editor hook, call:

    >>> get_ipython().set_hook('editor', yourfunc).

    """
    if not getattr(self, "editor", None):
        return

    editor = shlex.quote(self.editor)

    # marker for at which line to open the file (for existing objects)
    if linenum is None or editor == "notepad":
        linemark = ""
    else:
        linemark = "+%d" % int(linenum)

    # Call the actual editor
    proc = subprocess.Popen("%s %s %s" % (editor, linemark, filename), shell=True)
    if wait and proc.wait() != 0:
        raise TryNext()


class CommandChainDispatcher:
    """Dispatch calls to a chain of commands until some func can handle it.

    Usage
    ------
    - Instantiate

    - execute :meth:`add` to add commands (with optional priority parameter

    - execute normally via f() calling mechanism.

    """

    def __init__(self, chain=None):
        """Initialize.

        Parameters
        ----------
        chain : list
            Commands to try for a hook.

        """
        self.chain = chain or []

    def __call__(self, args=None, kw=None):
        """Command chain is called just like normal func.

        This will call all funcs in chain with the same args as were given to
        this function, and return the result of first func that didn't raise
        :exc:`TryNext`.

        .. note:: This doesn't utilize the priority in any way.ArithmeticError

            Maybe we need to do an sort using something in mod:`operator`.

        """
        for prio, cmd in self.chain:
            # print "prio",prio,"cmd",cmd #dbg
            try:
                return cmd(*args, **kw)
            except TryNext as exc:
                # if no function will accept it, raise TryNext up to the caller
                raise exc

    def __repr__(self):
        return "{!r}\n{!r}".format(self.__class__.__name__, self.chain)

    def add(self, func, priority=0):
        """ Add a func to the cmd chain with given priority """
        self.chain.append((priority, func))
        self.chain.sort(key=lambda x: x[0])

    def __iter__(self):
        """Return all objects in chain.

        Handy if the objects are not callable.
        """
        return iter(self.chain)


def shutdown_hook(self):
    """Default shutdown hook.

    Typically, shutdown hooks should raise TryNext so all shutdown ops are done
    """
    self.log("default shutdown hook ok")
    return


def late_startup_hook(self, *args, **kwargs):
    """Executed after ipython has been constructed and configured."""
    self.log("default startup hook ok")
    return


def show_in_pager(self, *, data=None, start=None, screen_lines=None):
    """Run a string through the pager.

    Idk what these parameters are though.

    Where does this get invoked by the way?

    .. note:: raising TryNext here will use the default paging functionality

    Parameters
    ----------
    self :
    data :
    start :
    screen_lines :

    """
    raise TryNext


def pre_prompt_hook(self):
    """Run before displaying the next prompt

    Use this e.g. to display output from asynchronous operations (in order
    to not mess up text entry).
    """
    return None


def pre_run_code_hook(self):
    """Executed before running the (prefiltered) code in IPython."""
    return None


def clipboard_get(self):
    """Get text from the clipboard."""
    from IPython.lib.clipboard import (
        osx_clipboard_get,
        tkinter_clipboard_get,
        win32_clipboard_get,
    )

    if sys.platform == "win32":
        chain = [win32_clipboard_get, tkinter_clipboard_get]
    elif sys.platform == "darwin":
        chain = [osx_clipboard_get, tkinter_clipboard_get]
    else:
        chain = [tkinter_clipboard_get]
    dispatcher = CommandChainDispatcher()
    for func in chain:
        dispatcher.add(func)
    text = dispatcher()
    return text


def synchronize_with_editor(self, filename, linenum, column):
    """

    Parameters
    ----------
    self :
    filename :
    linenum :
    column :
    """
    pass
