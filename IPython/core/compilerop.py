r"""Compiler tools with improved interactive support.

Provides compilation machinery similar to codeop, but with caching support so
we can provide interactive tracebacks.

Note: though it might be more natural to name this module 'compiler', that
name is in the stdlib and name collisions with the stdlib tend to produce
weird problems (often with third-party tools).

.. data:: PyCF_MASK

    Roughly equal to PyCF_MASK | PyCF_MASK_OBSOLETE as defined in pythonrun.h.
    This is used as a bitmask to extract future-related code flags.


Authors
-------
* Robert Kern
* Fernando Perez
* Thomas Kluyver


And here's the docstring from codeop.

Utilities to compile possibly incomplete Python source code.

This module provides two interfaces, broadly similar to the builtin
function compile(), which take program text, a filename and a 'mode'
and:

- Return code object if the command is complete and valid
- Return None if the command is incomplete
- Raise SyntaxError, ValueError or OverflowError if the command is a
  syntax error (OverflowError and ValueError can be produced by
  malformed literals).

Approach:

First, check if the source consists entirely of blank lines and
comments; if so, replace it with 'pass', because the built-in
parser doesn't always do the right thing for these.

Compile three times: as is, with \n, and with \n\n appended.  If it
compiles as is, it's complete.  If it compiles with one \n appended,
we expect more.  If it doesn't compile either way, we compare the
error we get when compiling with \n or \n\n appended.  If the errors
are the same, the code is broken.  But if the errors are different, we
expect more.  Not intuitive; not even guaranteed to hold in future
releases; but this matches the compiler's behavior from Python 1.4
through 2.2, at least.

Caveat:

It is possible (but not likely) that the parser stops parsing with a
successful outcome before reaching the end of the source; in this
case, trailing symbols may be ignored instead of causing an error.
For example, a backslash followed by two newlines may be followed by
arbitrary garbage.  This will be fixed once the API for the parser is
better.

The two interfaces are:

compile_command(source, filename, symbol):

    Compiles a single command in the manner described above.

CommandCompiler():

    Instances of this class have __call__ methods identical in
    signature to compile_command; the difference is that if the
    instance compiles program text containing a __future__ statement,
    the instance 'remembers' and compiles all subsequent program texts
    with the statement in force.

The module also provides another class:

Compile():

    Instances of this class act like the built-in function compile,
    but with 'memory' in the sense described above.

"""
# -----------------------------------------------------------------------------
#  Copyright (C) 2010-2011 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# Stdlib imports
import __future__

import codeop
import functools
import hashlib
import linecache
import operator
import time
from ast import PyCF_ONLY_AST
from codeop import _maybe_compile
from contextlib import contextmanager

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# What...
PyCF_MASK = functools.reduce(
    operator.or_,
    (
        getattr(__future__, fname).compiler_flag
        for fname in __future__.all_feature_names
    ),
)

# -----------------------------------------------------------------------------
# Local utilities
# -----------------------------------------------------------------------------


def code_name(code, number=0):
    """Compute a (probably) unique name for code for caching.

    This now expects code to be unicode. Utilizes :func:`haslib.sha`.

    Notes
    -----
    Includes the number and 12 characters of the hash in the name.  It's
    pretty much impossible that in a single session we'll have collisions
    even with truncated hashes, and the full one makes tracebacks too long
    """
    hash_digest = hashlib.sha1(code.encode("utf-8")).hexdigest()
    return "<ipython-input-{0}-{1}>".format(number, hash_digest[:12])


# -----------------------------------------------------------------------------
# Classes and functions
# -----------------------------------------------------------------------------


class CachingCompiler(codeop.Compile):
    """A compiler that caches code compiled from interactive statements.

    Notes
    -----
    This is ugly, but it must be done this way to allow multiple
    simultaneous ipython instances to coexist.  Since Python itself
    directly accesses the data structures in the linecache module, and
    the cache therein is global, we must work with that data structure.
    We must hold a reference to the original checkcache routine and call
    that in our own check_cache() below, but the special IPython cache
    must also be shared by all IPython instances.  If we were to hold
    separate caches (one in each CachingCompiler instance), any call made
    by Python itself to linecache.checkcache() would obliterate the
    cached data from the other IPython instances.::

        if not hasattr(linecache, "_ipython_cache"):
            linecache._ipython_cache = {}
        if not hasattr(linecache, "_checkcache_ori"):
            linecache._checkcache_ori = linecache.checkcache

    """

    def __init__(self, *args, **kwargs):
        """Added ``*args`` and ``**kwargs``."""
        self.compiler = codeop.Compile()
        self.reset_compiler_flags()
        # I would call super() here but super does the above 2 lines and that's it

        if not hasattr(linecache, "_ipython_cache"):
            linecache._ipython_cache = {}
        if not hasattr(linecache, "_checkcache_ori"):
            linecache._checkcache_ori = linecache.checkcache
        # Now, we must monkeypatch the linecache directly so that parts of the
        # stdlib that call it outside our control go through our codepath
        # (otherwise we'd lose our tracebacks).
        linecache.checkcache = self.check_linecache_ipython

    def __call__(self, source, filename="<input>", symbol="single"):
        r"""Compile a command and determine whether it is incomplete.

        Now this class is a callable.

        Arguments
        ---------
        source : str
            the source string; may contain \n characters
        filename : str, optional
            optional filename from which source was read;
            default "<input>"
        symbol : str, optional
            grammar start symbol; "single" (default) or "eval"

        Returns
        -------
        - Return a code object if the command is complete and valid
        - Return None if the command is incomplete

        Raises
        ------
        Raise SyntaxError, ValueError or OverflowError if the command is a
        syntax error (OverflowError and ValueError can be produced by
        malformed literals).

        """
        try:
            return super().__call__(source, filename, symbol)
        except (SyntaxError, ValueError, OverflowError):
            raise
        except UsageError:
            sys.stderr.write('UsageError')
            return

    def ast_parse(self, source, filename="<unknown>", symbol="exec"):
        """Parse code to an AST with the current compiler flags active.

        Arguments are exactly the same as ast.parse (in the standard library),
        and are passed to the built-in compile function."""
        return compile(source, filename, symbol, self.flags | PyCF_ONLY_AST, 1)

    def reset_compiler_flags(self):
        """Reset compiler flags to default state.

        Note
        ----
        Mirrors :func:`codeop.Compile.__init__`.

        """
        self.flags = codeop.PyCF_DONT_IMPLY_DEDENT

    @property
    def compiler_flags(self):
        """Flags currently active in the compilation process."""
        return self.flags

    def cache(self, code, number=0):
        """Make a name for a block of code, and cache the code.

        Parameters
        ----------
        code : str
          The Python source code to cache.
        number : int
          A number which forms part of the code's name. Used for the execution
          counter.

        Returns
        -------
        The name of the cached code (as a string). Pass this as the filename
        argument to compilation, so that tracebacks are correctly hooked up.
        """
        name = code_name(code, number)
        entry = (
            len(code),
            time.time(),
            [line + "\n" for line in code.splitlines()],
            name,
        )
        linecache.cache[name] = entry
        linecache._ipython_cache[name] = entry
        return name

    @contextmanager
    def extra_flags(self, flags):
        """

        Parameters
        ----------
        flags :
        """
        # bits that we'll set to 1
        turn_on_bits = ~self.flags & flags

        self.flags = self.flags | flags
        try:
            yield
        finally:
            # turn off only the bits we turned on so that something like
            # __future__ that set flags stays.
            self.flags &= ~turn_on_bits

    @staticmethod
    def check_linecache_ipython(*args):
        """Call linecache.checkcache() safely protecting our cached values.

        This is getting moved into the class as a staticmethod because
        it literally depends on the linecache updates we make in the init.

        There's a state where we don't initialize and this gets imported
        and runs and that'll get called incorrectly.
        """
        # First call the original checkcache as intended
        linecache._checkcache_ori(*args)
        # Then, update back the cache with our data, so that tracebacks related
        # to our compiled codes can be produced.
        linecache.cache.update(linecache._ipython_cache)
