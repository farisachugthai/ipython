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

from IPython.core.error import ClipboardEmpty, TryNext
from IPython.utils.ipstruct import Struct

__all__ = [
    "shutdown_hook",
    "late_startup_hook",
    "show_in_pager",
    "pre_prompt_hook",
    "deprecated",
    "pre_run_code_hook",
]


class CommandChainDispatcher(Struct):
    """Dispatch calls to a chain of commands until some func can handle it.

    Usage
    ------
    - Instantiate

    - execute :meth:`add` to add commands (with optional priority parameter

    - execute normally via f() calling mechanism.

    """

    def __init__(self, chain=None, *args, **kwargs):
        """Initialize.

        Parameters
        ----------
        chain : list
            Commands to try for a hook.

        """
        super().__init__(*args, **kwargs)
        self.chain = chain or []

    def call(self, *args, **kw):
        """Command chain is called just like normal func.

        This will call all funcs in chain with the same args as were given to
        this function, and return the result of first func that didn't raise
        :exc:`TryNext`.

        .. note:: This doesn't utilize the priority in any way.

        .. todo:: Maybe we need to do a sort using something in mod:`operator`.

        """
        if args is None and kw is None:
            return
        last_exc = TryNext()
        for prio, cmd in self.chain:
            # print "prio",prio,"cmd",cmd #dbg
            try:
                return cmd(args, kw)
            except TryNext as exc:
                last_exc = exc
        # if no function will accept it, raise TryNext up to the caller
        raise last_exc

    def __repr__(self):
        return "{!r}:\n{!r}".format(self.__class__.__name__, self.chain)

    def add(self, func, priority=0):
        """ Add a func to the cmd chain with given priority """
        self.chain.append((priority, func))
        self.chain.sort(key=lambda x: x[0])

    def __iter__(self):
        """Return all objects in chain.

        Handy if the objects are not callable.
        """
        return iter(self.chain)

    def __add__(self, func, priority=0):
        return self.add(func, priority)

    def __call__(self, *args, **kw):
        return self.call(args, kw)


def shutdown_hook(self, *args, **kwargs):
    """Default shutdown hook.

    Typically, shutdown hooks should raise TryNext so all shutdown ops are done
    """
    return


def late_startup_hook(self, *args, **kwargs):
    """Executed after ipython has been constructed and configured."""
    if getattr(self, "log", None):
        self.log.info("default startup hook ok")
    return


def show_in_pager(self, *args, data=None, start=None, screen_lines=None, **kwargs):
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


def pre_prompt_hook(self, *args, **kwargs):
    """Run before displaying the next prompt

    Use this e.g. to display output from asynchronous operations (in order
    to not mess up text entry).
    """
    return None


def pre_run_code_hook(self, *args, **kwargs):
    """Executed before running the (prefiltered) code in IPython."""
    return None


def deprecated(self, *args, **kwargs):
    """This feels silly don't you think?"""
    pass
