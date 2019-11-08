# encoding: utf-8
"""
Global exception classes for IPython.core.

Authors:

* Brian Granger
* Fernando Perez
* Min Ragan-Kelley

Notes
-----

Nov 01, 2019:

So this was previously in `./magics/basic` inside of the `%colors` magic.
Why would you not simply make it an error that subclasses
`UsageError` so nothing crashes?::

    def color_switch_err(name):
        warn('Error changing %s color schemes.\n%s' %
                (name, sys.exc_info()[1]),
                stacklevel=2)


"""

# -----------------------------------------------------------------------------
#  Copyright (C) 2008 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Exception classes
# -----------------------------------------------------------------------------


class IPythonCoreError(Exception):
    pass


class TryNext(IPythonCoreError):
    """Try next hook exception.

    Raise this in your hook function to indicate that the next hook handler
    should be used to handle the operation.
    """
    pass


class UsageError(IPythonCoreError):
    """Error in magic function arguments, etc.

    Something that probably won't warrant a full traceback, but should
    nevertheless interrupt a macro / batch file.
    """
    pass


class StdinNotImplementedError(IPythonCoreError, NotImplementedError):
    """raw_input was requested in a context where it is not supported

    For use in IPython kernels, where only some frontends may support
    stdin requests.
    """


class InputRejected(Exception):
    """Input rejected by ast transformer.

    Raise this in your NodeTransformer to indicate that InteractiveShell should
    not execute the supplied input.
    """


class AliasError(Exception):
    """Oct 24, 2019: Moved from `IPython.core.alias`."""
    pass


class InvalidAliasError(AliasError):
    pass


class KillEmbedded(Exception):
    """This one's from `IPython.terminal.embed`."""
    pass


class ColorSwitchErr(UsageError):
    """Nov 01, 2019: From ./magics/basic"""
    def __call__(self):
        if sys.exc_info:
            return ''.format(sys.exc_info())

    def warn(self, name):
        return 'Error changing {} color schemes.\n{}'.format(
            name,
            sys.exc_info()[1])
