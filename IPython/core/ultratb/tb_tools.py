import abc
import sys

from IPython.core.excolors import exception_colors
from IPython.utils.PyColorize import Colorable


class TBToolsABC(abc.ABC):
    """Refactored the :meth:`structured_traceback` method out of TBTools.

    Seemed more sensible to make it an ABC class.
    """

    @abc.abstractmethod
    def structured_traceback(
        self, etype, evalue, tb, tb_offset=None, context=5, mode=None
    ):
        """Return a list of traceback frames.

        Must be implemented by each class.

        See Also
        --------
        :class:`~AutoFormattedTB`.
        :class:`~SyntaxTB`.

        """
        raise NotImplementedError()


class TBTools(Colorable):
    """Basic tools used by all traceback printer classes.

    Attributes
    ----------
    ostream : :class:`_io.TextIOWrapper`.
        Output stream to write to.  Note that we store the original value in
        a private attribute and then make the public ostream a property, so
        that we can delay accessing sys.stdout until runtime.  The way
        things are written now, the sys.stdout object is dynamically managed
        so a reference to it should NEVER be stored statically.  This
        property approach confines this detail to a single location, and all
        subclasses can simply access self.ostream for writing.

    tb_offset : int
        Defaults to 0.
        Number of frames to skip when reporting tracebacks.

    color_scheme_table : Dict
        :func:`IPython.core.excolors.exception_colors` output.

    call_pdb : bool
        Needs to be next var refactored out of here.
        Like whose idea was it to implement color management, exception
        handling, debugging, user interaction, user configuration, traceback
        formatting, and differentiating exceptions based on cause IN ONE CLASS.

    """

    tb_offset = 0

    def __init__(
        self,
        color_scheme="LightBG",
        call_pdb=False,
        ostream=None,
        parent=None,
        config=None,
    ):
        """
        Parameters
        ----------
        color_scheme : str
            Maybe a colorscheme as defined by IPython.utils.ColorScheme
        call_pdb : bool
            Whether to invoke the debugger after an exception
        ostream : io.TextStream
            Might be the type. Something similar to sys.stdout.
        parent : :class:`IPython.core.interactiveshell.InteractiveShell`
            Global IPython instance
        config : :class:`traitlets.config.Config`
            Dict of user configs.

        """
        super().__init__(parent=parent, config=config)

        # Create color table
        # self.color_scheme_table = exception_colors()

        self.color_scheme = color_scheme
        if not hasattr(self, "color_scheme_table"):
            self.color_scheme_table = exception_colors()

        if hasattr(self.color_scheme_table, "active_colors"):
            self.Colors = self.color_scheme_table.active_colors
        # else:
        #     self.color_scheme_table = ColorSchemeTable()

        # self.set_colors(color_scheme)
        # self.old_scheme = color_scheme  # save initial value for toggles

        self.call_pdb = call_pdb
        self._ostream = ostream

        from IPython.core import debugger

        self.pdb = debugger.CorePdb() if self.call_pdb else None

    def __repr__(self):
        """This isn't defined like anywhere. Let's do everyone a favor."""
        return "".join(self.__class__.__name__)

    def _get_ostream(self):
        """Output stream that exceptions are written to.

        Valid values are:

        - None: the default, which means that IPython will dynamically resolve
          to sys.stdout.  This ensures compatibility with most tools, including
          Windows (where plain stdout doesn't recognize ANSI escapes).

        - Any object with 'write' and 'flush' attributes.

        """
        return sys.stdout if self._ostream is None else self._ostream

    def _set_ostream(self, val):
        assert val is None or (hasattr(val, "write") and hasattr(val, "flush"))
        self._ostream = val

    ostream = property(_get_ostream, _set_ostream)

    def get_parts_of_chained_exception(self, evalue):
        def get_chained_exception(exception_value):
            cause = getattr(exception_value, "__cause__", None)
            if cause:
                return cause
            if getattr(exception_value, "__suppress_context__", False):
                return None
            return getattr(exception_value, "__context__", None)

        chained_evalue = get_chained_exception(evalue)

        if chained_evalue:
            return (
                chained_evalue.__class__,
                chained_evalue,
                chained_evalue.__traceback__,
            )

    def prepare_chained_exception_message(self, cause):
        direct_cause = (
            "\nThe above exception was the direct cause of the following exception:\n"
        )
        exception_during_handling = (
            "\nDuring handling of the above exception, another exception occurred:\n"
        )

        if cause:
            message = [[direct_cause]]
        else:
            message = [[exception_during_handling]]
        return message

    def set_colors(self, *args, **kw):
        """Shorthand access to the color table scheme selector method."""

        # Set own color table
        # self.color_scheme_table.set_active_scheme(*args, **kw)
        # for convenience, set Colors to the active scheme

        # Also set colors of debugger
        if hasattr(self, "pdb") and self.pdb is not None:
            if getattr(self.pdb, "set_colors", None):
                self.pdb.set_colors(*args, **kw)

    def color_toggle(self):
        """Toggle between the currently active color scheme and NoColor."""

        if self.color_scheme_table.active_scheme_name == "NoColor":
            self.color_scheme_table.set_active_scheme(self.old_scheme)
            self.Colors = self.color_scheme_table.active_colors
        else:
            self.old_scheme = self.color_scheme_table.active_scheme_name
            self.color_scheme_table.set_active_scheme("NoColor")
            self.Colors = self.color_scheme_table.active_colors

    def stb2text(self, stb):
        """Convert a structured traceback (a list) to a string."""
        return "\n".join(stb)

    def text(self, etype, value, tb, tb_offset=None, context=5):
        """Return formatted traceback.

        Subclasses may override this if they add extra arguments.
        """
        tb_list = self.structured_traceback(etype, value, tb, tb_offset, context)
        return self.stb2text(tb_list)
