"""Tests for debugging machinery.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
import warnings

import nose.tools as nt

from IPython.core import debugger

# -----------------------------------------------------------------------------
# Helper classes, from CPython's Pdb test suite
# -----------------------------------------------------------------------------


class _FakeInput(object):
    """
    A fake input stream for pdb's interactive debugger.  Whenever a
    line is read, print it (to simulate the user typing it), and then
    return it.  The set of lines to return is specified in the
    constructor; they should not have trailing newlines.
    """
    def __init__(self, lines):
        self.lines = iter(lines)

    def readline(self):
        line = next(self.lines)
        print(line)
        return line + '\n'


class PdbTestInput(object):
    """Context manager that makes testing Pdb in doctests easier."""
    def __init__(self, input):
        self.input = input

    def __enter__(self):
        self.real_stdin = sys.stdin
        sys.stdin = _FakeInput(self.input)

    def __exit__(self, *exc):
        sys.stdin = self.real_stdin


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_longer_repr():
    try:
        from reprlib import repr as trepr  # Py 3
    except ImportError:
        from repr import repr as trepr  # Py 2

    a = '1234567890' * 7
    ar = "'1234567890123456789012345678901234567890123456789012345678901234567890'"
    a_trunc = "'123456789012...8901234567890'"
    nt.assert_equal(trepr(a), a_trunc)
    # The creation of our tracer modifies the repr module's repr function
    # in-place, since that global is used directly by the stdlib's pdb module.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        debugger.Tracer()
    nt.assert_equal(trepr(a), ar)


def test_ipdb_magics():
    """Test calling some IPython magics from ipdb.

    First, set up some test functions and classes which we can inspect.

    >>> class ExampleClass(object):
    ...    """


def test_ipdb_magics2():
    """Test ipdb with a very short function.

    >>> old_trace = sys.gettrace()

    >>> def bar():
    ...     pass

    Run ipdb.

    >>> with PdbTestInput([
    ...    'continue',
    ... ]):
    ...     debugger.Pdb().runcall(bar)
    > <doctest ...>(2)bar()
          1 def bar():
    ----> 2    pass
    <BLANKLINE>
    ipdb> continue

    Restore previous trace function, e.g. for coverage.py

    >>> sys.settrace(old_trace)
    """


def can_quit():
    """Test that quit work in ipydb

    >>> old_trace = sys.gettrace()

    >>> def bar():
    ...     pass

    >>> with PdbTestInput([
    ...    'quit',
    ... ]):
    ...     debugger.Pdb().runcall(bar)
    > <doctest ...>(2)bar()
            1 def bar():
    ----> 2    pass
    <BLANKLINE>
    ipdb> quit

    Restore previous trace function, e.g. for coverage.py

    >>> sys.settrace(old_trace)
    """


def can_exit():
    """Test that quit work in ipydb

    >>> old_trace = sys.gettrace()

    >>> def bar():
    ...     pass

    >>> with PdbTestInput([
    ...    'exit',
    ... ]):
    ...     debugger.Pdb().runcall(bar)
    > <doctest ...>(2)bar()
            1 def bar():
    ----> 2    pass
    <BLANKLINE>
    ipdb> exit

    Restore previous trace function, e.g. for coverage.py

    >>> sys.settrace(old_trace)
    """
