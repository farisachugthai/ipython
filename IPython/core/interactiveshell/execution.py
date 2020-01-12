import code
import reprlib
import sys
import types
from types import CodeType, FunctionType

from traitlets.traitlets import Bool, Instance
from traitlets.config import LoggingConfigurable

if sys.version_info < (3, 7):
    from IPython.core.error import ModuleNotFoundError


def get_cells(fname):
    """Generator for sequence of code blocks to run.

    .. versionchanged:: 7.11.0

        Now also checks that we didn't get passed a file handle by accident.

    Parameters
    ----------
    fname : str (os.Pathlike)
        Path to filename.

    Yields
    ------
    Lines of file

    Notes
    -----
    Depends on nbformat
    """
    if getattr(fname, "read", None):
        yield fname.read()
    if fname.endswith(".ipynb"):
        try:
            from nbformat import read
        except (ImportError, ModuleNotFoundError):
            raise

        nb = read(fname, as_version=4)
        if not nb.cells:
            return
        for cell in nb.cells:
            if cell.cell_type == "code":
                yield cell.source
    else:
        with open(fname) as f:
            yield f.read()


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
    pass


class DummyMod:
    """A dummy module used for IPython's interactive module when
    a namespace must be assigned to the module's __dict__.

    .. todo:: collections.NamedTuple?
    """

    __spec__ = None


class ExecutionInfo(LoggingConfigurable):
    """The arguments used for a call to :meth:`InteractiveShell.run_cell`.

    Stores information about what is going to happen.

    """

    store_history = Bool(True, help="Whether to log ExecutionInfo or not.").tag(
        config=True
    )

    shell = Instance("IPython.core.interactiveshell.InteractiveShellABC")

    silent = Bool(False, help="Stream log info to stdout as well?").tag(config=True)

    shell_futures = Bool(
        True,
        help="I've been working on this for too long to have to say I have no idea.",
    ).tag(config=True)

    def __init__(self, raw_cell, *args, **kwargs):
        self.raw_cell = raw_cell
        self.truncated_cell = reprlib.Repr().repr(self.raw_cell)
        super().__init__(**kwargs)

    def repr(self):
        """Public method for the repr.

        Just to make it easier to see in a ``ExecutionResult?`` in the REPL.
        Also let's embrance string formatting!

        """
        # TODO: Check the unittests and then start deleting all the BS out of this.
        return """
        <{} object at {}
        raw_cell={}
        store_history={} silent={} shell_futures={}>""".format(
            self.__class__.__name__,
            id(self),
            self.truncated_cell,
            self.store_history,
            self.silent,
            self.shell_futures,
        )

    def __repr__(self):
        return self.repr()


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

    def __init__(self, info=None, *args, **kwargs):
        self.info = info

    def error_before_exec(self, value):
        """Wait does that say result.error_before_exec wait what the fuck.

        Moved this over here. Idk if I was supposed to. Check soon.
        """
        if not self.quiet:
            self.execution_count += 1
        result = self.get_result()
        result.error_before_exec = value
        self.last_execution_succeeded = False
        self.last_execution_result = result
        return result

    @property
    def success(self):
        return (self.error_before_exec is None) and (self.error_in_exec is None)

    def raise_error(self):
        """Reraises error if `success` is `False`, otherwise does nothing"""
        if self.error_before_exec is not None:
            raise self.error_before_exec
        if self.error_in_exec is not None:
            raise self.error_in_exec

    # def __repr__(self):
    #     return (
    #         "<%s object at %x, execution_count=%s error_before_exec=%s error_in_exec=%s info=%s result=%s>"
    #         % (
    #             self.__class__.__qualname__,
    #             id(self),
    #             self.execution_count,
    #             self.error_before_exec,
    #             self.error_in_exec,
    #             self.info,
    #             self.result,
    #         )
    #     )
