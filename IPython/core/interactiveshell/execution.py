import sys
import types
from types import CodeType, FunctionType


def removed_co_newlocals(function: types.FunctionType) -> types.FunctionType:
    """Return a function that do not create a new local scope.

    Given a function, create a clone of this function where the co_newlocal flag
    has been removed, making this function code actually run in the sourounding
    scope.

    We need this in order to run asynchronous code in user level namespace.
    """
    CO_NEWLOCALS = 0x0002
    code = function.__code__
    new_co_flags = code.co_flags & ~CO_NEWLOCALS
    if sys.version_info > (3, 8, 0, "alpha", 3):
        new_code = code.replace(co_flags=new_co_flags)
    else:
        new_code = CodeType(
            code.co_argcount,
            code.co_kwonlyargcount,
            code.co_nlocals,
            code.co_stacksize,
            new_co_flags,
            code.co_code,
            code.co_consts,
            code.co_names,
            code.co_varnames,
            code.co_filename,
            code.co_name,
            code.co_firstlineno,
            code.co_lnotab,
            code.co_freevars,
            code.co_cellvars,
        )
    return FunctionType(new_code, globals(), function.__name__, function.__defaults__)


def softspace(file, newvalue):
    """Copied from code.py, to remove the dependency

    Parameters
    ----------
    file :
    newvalue :
    """
    oldvalue = 0
    try:
        oldvalue = file.softspace
    except AttributeError:
        pass
    try:
        file.softspace = newvalue
    except (AttributeError, TypeError):
        # "attribute-less object" or "read-only attributes"
        pass
    return oldvalue


def no_op(*a, **kw):
    """

    Parameters
    ----------
    a :
    kw :
    """
    pass


class DummyMod:
    """A dummy module used for IPython's interactive module when
    a namespace must be assigned to the module's __dict__."""

    __spec__ = None


class ExecutionInfo:
    """The arguments used for a call to :meth:`InteractiveShell.run_cell`.

    Stores information about what is going to happen.

    """

    def __init__(
        self, raw_cell=None, store_history=False, silent=False, shell_futures=True
    ):
        self.raw_cell = raw_cell
        self.store_history = store_history
        self.silent = silent
        self.shell_futures = shell_futures

    def __repr__(self):
        name = self.__class__.__qualname__
        raw_cell = (
            (self.raw_cell[:50] + "..") if len(self.raw_cell) > 50 else self.raw_cell
        )
        return (
            '<%s object at %x, raw_cell="%s" store_history=%s silent=%s shell_futures=%s>'
            % (
                name,
                id(self),
                raw_cell,
                self.store_history,
                self.silent,
                self.shell_futures,
            )
        )


class ExecutionResult:
    """The result of a call to :meth:`InteractiveShell.run_cell`

    Stores information about what took place.

    .. todo:: Check out if this wouldn't be better implemented as a dataclass.

    Attributes
    ----------
    execution_count = None
    error_before_exec = None
    error_in_exec = None
    info = None
    result = None

    Parameters
    ----------
    execution_count = None
    error_before_exec = None
    error_in_exec = None
    result = None

    """

    execution_count = None
    error_before_exec = None
    error_in_exec = None
    result = None

    def __init__(self, info=None):
        self.info = info

    @property
    def success(self):
        """

        Returns
        -------

        """
        return (self.error_before_exec is None) and (self.error_in_exec is None)

    def raise_error(self):
        """Reraises error if `success` is `False`, otherwise does nothing"""
        if self.error_before_exec is not None:
            raise self.error_before_exec
        if self.error_in_exec is not None:
            raise self.error_in_exec

    def __repr__(self):
        name = self.__class__.__qualname__
        return (
            "<%s object at %x, execution_count=%s error_before_exec=%s error_in_exec=%s info=%s result=%s>"
            % (
                name,
                id(self),
                self.execution_count,
                self.error_before_exec,
                self.error_in_exec,
                repr(self.info),
                repr(self.result),
            )
        )

