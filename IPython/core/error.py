# encoding: utf-8
"""
Global exception classes for IPython.core.

Authors:

* Brian Granger
* Fernando Perez
* Min Ragan-Kelley

"""
import bdb
import sys


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

    Raise this in your :class:`ast.NodeTransformer` to indicate that
    :class:`~IPython.core.interactiveshell.InteractiveShell` should
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
    r"""Nov 01, 2019: From ./magics/basic.

    Here's the original.:

        def color_switch_err(name):
            warn('Error changing %s color schemes.\n%s' %
                 (name, sys.exc_info()[1]),
                 stacklevel=2)
    """

    @property
    def __traceback__(self):
        """So I think exceptions usually have this defined now right?"""
        return super().__traceback__

    def __repr__(self):
        return "".format(self.__class__.__name)

    def __call__(self, name):
        return "{}:\nError changing {} color schemes.\n{}".format(
            repr(self), name, sys.exc_info()
        )


class XmodeSwitchErr(ColorSwitchErr):
    r"""Also from magics/basic.

    ::

        def xmode_switch_err(name):
            warn('Error changing %s exception modes.\n%s' %
                 (name, sys.exc_info()[1]))

    """

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class ProvisionalWarning(DeprecationWarning):
    """Warning class for unstable features. Moved out of ./interactiveshell.py."""

    pass


class SpaceInInput(Exception):
    """Interactiveshell."""

    pass


class ProvisionalCompleterWarning(FutureWarning):
    """Exception raise by an experimental feature in this module.

    Wrap code in :class:`~IPython.core.completerlib.ProvisionalCompleter`
    context manager if you are certain you want to use an unstable feature.

    From completerlib.
    """

    pass


class MacroToEdit(ValueError):
    """Used for exception handling in magic_edit. Nov 13, 2019: ./magics/code.py"""

    pass


class InteractivelyDefined(Exception):
    """Exception for interactively defined variable in magic_edit"""

    def __init__(self, index):
        self.index = index


if sys.version_info[0:2] < (3, 7):

    class ModuleNotFoundError(ImportError):
        """Backport and define ModuleNotFound so we can catch it later."""

        __module__ = "builtins"  # for py3

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def __repr__(self):
            return "{}\n{}".format(self.__class__.__name__, self.__traceback__)


def BdbQuit_excepthook(et, ev, tb, excepthook=None):
    """Exception hook which handles `BdbQuit` exceptions.

    All other exceptions are processed using the `excepthook`
    parameter.
    """
    if et == bdb.BdbQuit:
        print("Exiting Debugger.")
    elif excepthook is not None:
        excepthook(et, ev, tb)
    else:
        # Backwards compatibility. Raise deprecation warning?
        BdbQuit_excepthook.excepthook_ori(et, ev, tb)


def BdbQuit_IPython_excepthook():
    print("Exiting Debugger.")


class DatabaseError(Exception):
    """Dummy exception when sqlite could not be imported. Should never occur.

    Actually happened to me from some misplaced dlls on Windows.
    Moved from :mod:`history`.
    """

    def __init__(self, *args, **kwargs):
        super().__init(self, *args, **kwargs)


class OperationalError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init(self, *args, **kwargs)


class UnknownBackend(KeyError):
    """terminal/pt_inputhooks/__init__"""

    def __init__(self, name):
        """Name?"""
        self.name = name

    def __str__(self):
        return (
            "No event loop integration for {!r}. " "Supported event loops are: {}"
        ).format(self.name, ", ".join(backends + sorted(registered)))


class ShimWarning(Warning):
    """A warning to show when a module has moved, and a shim is in its place.

    IPython/utils/shimmodule: Dec 02, 2019
    """

    pass


class ClipboardEmpty(ValueError):
    """lib.clipboard"""

    def __call__(self, msg=None):
        if msg is None:
            pass
        else:
            print(msg)


class ProfileDirError(Exception):
    """./profiledir"""

    def __init__(self, bad_profile=None, *args, **kwargs):
        """Location of the profile that raised the error and a message to pass along to Exception."""
        self.bad_profile = bad_profile
        super().__init__(self, *args, **kwargs)

    def __call__(self, msg=None):
        """Idk if it was a good idea to do it this way but we don't see our own errors."""
        if msg is None:
            # TODO: log
            pass
        else:
            print(msg)
        if self.bad_profile is not None:
            print("Location of the faulty profile. {}".format(self.bad_profile))
        return msg

    def __repr__(self, msg=None):
        if msg is None:
            msg = ""
        return "{}\t{}".format(self.__class__.__name__, msg)


class DemoError(Exception):

    pass


class DerivedInterrupt(KeyboardInterrupt):
    """interactiveshell.tests.test_interactiveshell"""

    pass


class DataIsObject(Exception):
    """magics.code"""
    # custom exceptions
    pass

