import linecache
import sys
import traceback

from IPython.core.error import OperationalError
from IPython.utils.coloransi import ColorSchemeTable

from .tb_tools import TBTools


class ListTB(TBTools):
    """Print traceback information from a traceback list with optional color.

    Calling requires 3 arguments as would be obtained by::

        etype, evalue, tb = sys.exc_info()
        if tb:
            elist = traceback.extract_tb(tb)
        else:
            elist = None

    It can thus be used by programs which need to process the traceback before
    printing (such as console replacements based on the :mod:`code` module
    from the standard library).

    Because they are meant to be called without a full traceback (only a
    `list`), instances of this class can't call the interactive `pdb` debugger.

    Parameters
    ----------
    # (etype, evalue, elist)
    Wait why did I have that listed as the parameters?
    color_scheme
    call_pdb
    ostream
    parent
    config
    TODO: Colors
        Missing a parameter that is used in
        :meth:`structured_traceback`.

    """

    def __init__(
        self,
        color_scheme="NoColor",
        call_pdb=False,
        ostream=None,
        parent=None,
        config=None,
    ):
        self.color_scheme = color_scheme
        self.call_pdb = call_pdb
        self.ostream = ostream
        self.parent = parent
        self.config = config

        TBTools.__init__(
            self,
            color_scheme=self.color_scheme,
            call_pdb=self.call_pdb,
            ostream=self.ostream,
            parent=self.parent,
            config=self.config,
        )

    def __call__(self, etype=None, value=None, elist=None):
        """How to invoke the tbtool.

        Wait wait what. What the hell is self.text?

        Got it! It's a method from `TBTools`.

        11/29/2019:

        Changing all the parameters to optional. If the user doesn't provide
        them, check sys.exc_info
        """
        if hasattr(self.ostream, "flush"):
            self.ostream.flush()
        else:
            raise OperationalError(
                "%s: ListTB.__call__ does not have an output stream.", __file__
            )
        # so i made this mistake a bunch of times throughout the repository
        # sys always have exc_info, sometimes it just returns (None, None, None)
        self.ostream.write(self.text(*sys.exc_info()) + "\n")

    def structured_traceback(
        self, etype=None, value=None, elist=None, tb_offset=None, context=5, mode=None
    ):
        """Return a color formatted string with the traceback info.

        Notes
        -----
        This is a workaround to get chained_exc_ids in recursive calls
        etb should not be a tuple if structured_traceback is not recursive.

        Parameters
        ----------
        mode :
        etype : exception type
            Type of the exception raised.
        value : object
            Data stored in the exception
        elist : list
            List of frames, see class docstring for details.
        tb_offset : int, optional
            Number of frames in the traceback to skip.  If not given, the
            instance value is used (set in constructor).
        context : int, optional
            Number of lines of context information to print.

        Returns
        -------
        out_list : str
            String with formatted exception.

        """
        if isinstance(etb, tuple):
            etb, chained_exc_ids = etb
        else:
            chained_exc_ids = set()

        if isinstance(etb, list):
            elist = etb
        elif etb is not None:
            elist = self._extract_tb(etb)
        else:
            elist = []

        if getattr(self, "Colors", None):
            Colors = self.Colors
        else:
            raise

        tb_offset = self.tb_offset if tb_offset is None else tb_offset
        out_list = []

        if elist:
            if tb_offset and len(elist) > tb_offset:
                elist = elist[tb_offset:]

            out_list.append(
                "Traceback %s(most recent call last)%s:"
                % (Colors.normalEm, Colors.Normal)
                + "\n"
            )
            out_list.extend(self._format_list(elist))
        # The exception info should be a single entry in the list.
        # lines = "".join(self._format_exception_only(etype, value))

        # exception = self.get_parts_of_chained_exception(evalue)

        # if exception and not id(exception[1]) in chained_exc_ids:
        #     chained_exception_message = self.prepare_chained_exception_message(
        #         evalue.__cause__)[0]
        #     etype, evalue, etb = exception
        #     # Trace exception to avoid infinite 'cause' loop
        #     chained_exc_ids.add(id(exception[1]))
        #     chained_exceptions_tb_offset = 0
        #     out_list = (
        #         self.structured_traceback(
        #             etype, evalue, (etb, chained_exc_ids),
        #             chained_exceptions_tb_offset, context)
        #         + chained_exception_message
        #         + out_list)
        # out_list.append(lines)

        return out_list

    def _format_list(self, extracted_list):
        """Format a list of traceback entry tuples for printing.

        Given a list of tuples as returned by extract_tb() or
        extract_stack(), return a list of strings ready for printing.
        Each string in the resulting list corresponds to the item with the
        same index in the argument list.  Each string ends in a newline;
        the strings may contain internal newlines as well, for those items
        whose source text line is not None.

        Lifted almost verbatim from traceback.py

        ...?
        """
        return traceback.format_list(extracted_list)

    def _format_exception_only(self):
        """Format the exception part of a traceback.

        Also lifted nearly verbatim from traceback.py

        Well now it simply returns it. It's not like this method wasn't already
        static.
        """
        etype, evalue, _ = sys.exc_info()
        return traceback.format_exception_only(etype, evalue)

    def get_exception_only(self, etype, value):
        """Only print the exception type and message, without a traceback.

        Parameters
        ----------
        etype : exception type
        value : exception value
        """
        return ListTB.structured_traceback(self, etype, value, [],)

    def show_exception_only(self, etype, evalue):
        """Only print the exception type and message, without a traceback.

        .. caution::

            This method needs to use __call__ from *this* class, not the one
            from a subclass whose signature or behavior may be different.

        Parameters
        ----------
        evalue :
        etype : exception type

        """
        self.ostream.flush()
        self.ostream.write("\n".join(traceback.format_exception_only(etype, evalue)))
        self.ostream.flush()

    @staticmethod
    def _some_str(self, value):
        """Now it literally returns :func:`traceback._some_str`."""
        return traceback._some_str(value)


class SyntaxTB(ListTB):
    """Extension which holds some state: the last exception value."""

    def __init__(self, color_scheme=None, parent=None, config=None):
        """Initialize SyntaxTB.

        Parameters
        ----------
        color_scheme : object
        parent : shell
            IPython instance
        config : :class:`traitlets.config.Config`
            Global config instance.

        """
        self.color_scheme_table = ColorSchemeTable()
        self.color_scheme = color_scheme or "Linux"
        self.parent = parent
        self.config = config
        # The 2 lines below are all that are in upstreams copy
        ListTB.__init__(
            self, color_scheme=self.color_scheme, parent=self.parent, config=self.config
        )
        self.last_syntax_error = None

    def __call__(self, value):
        self.last_syntax_error = value
        ListTB.__call__(self, *sys.exc_info())

    def structured_traceback(
        self, etype, value, elist, tb_offset=None, context=5, **kwargs
    ):
        """
        If the source file has been edited, the line in the syntax error can
        be wrong (retrieved from an outdated cache). This replaces it with
        the current value.
        """
        if (
            isinstance(value, SyntaxError)
            and isinstance(value.filename, str)
            and isinstance(value.lineno, int)
        ):
            linecache.checkcache(value.filename)
            newtext = linecache.getline(value.filename, value.lineno)
            if newtext:
                value.text = newtext
        self.last_syntax_error = value
        return super().structured_traceback(
            etype, value, elist, tb_offset=tb_offset, context=context
        )

    def clear_err_state(self):
        """Return the current error state and clear it"""
        e = self.last_syntax_error
        self.last_syntax_error = None
        return e

    def stb2text(self, stb):
        """Convert a structured traceback (a list) to a string."""
        return "".join(stb)
