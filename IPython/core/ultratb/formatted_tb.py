import sys
import traceback

from IPython.core.excolors import exception_colors

from .list_tb import ListTB
from .verbose_tb import VerboseTB


class FormattedTB(VerboseTB, ListTB):
    """Subclass ListTB but allow calling with a traceback.

    It can thus be used as a sys.excepthook for Python > 2.1.

    Also adds 'Context' and 'Verbose' modes, not available in ListTB.

    Allows a tb_offset to be specified. This is useful for situations where
    one needs to remove a number of topmost frames from the traceback (such as
    occurs with python programs that themselves execute other python code,
    like Python shells).

    Notes
    -----
    Outside of the diamond inheritance we have going on, this is also the class
    where we introduce the xmode parameter to the shell.
    Like these classes couldn't have more going on if they tried.
    Break that up into a new block of code.

    """

    def __init__(
        self,
        mode: str = "Plain",
        color_scheme: object = "Linux",
        call_pdb: bool = False,
        ostream: object = None,
        tb_offset: int = 0,
        long_header: bool = False,
        include_vars: bool = False,
        check_cache: object = None,
        debugger_cls: object = None,
        parent: object = None,
        config: object = None,
    ) -> object:
        """So wait what's the point of rewriting the __init__ if it's just the same as the superclasses."""

        # NEVER change the order of this list. Put new modes at the end:
        self.valid_modes = ["Plain", "Context", "Verbose", "Minimal"]
        self.verbose_modes = self.valid_modes[1:3]

        # why did i comment this out?
        # self.color_scheme_table = exception_colors()
        if hasattr(self, "color_scheme_table"):
            if hasattr(self.color_scheme_table, "active_colors"):
                self.Colors = self.color_scheme_table.active_colors
        else:
            self.color_scheme_table = exception_colors()

        super().__init__(
            self,
            color_scheme=color_scheme,
            call_pdb=call_pdb,
            ostream=ostream,
            tb_offset=tb_offset,
            long_header=long_header,
            include_vars=include_vars,
            check_cache=check_cache,
            debugger_cls=debugger_cls,
            parent=parent,
            config=config,
        )

        # Different types of tracebacks are joined with different separators to
        # form a single string.  They are taken from this dict
        self._join_chars = dict(Plain="", Context="\n", Verbose="\n", Minimal="")
        # set_mode also sets the tb_join_char attribute
        self.set_mode(mode)

    def _extract_tb(self, tb=None):
        if tb:
            return traceback.extract_tb(tb)
        else:
            return None

    def structured_traceback(
        self, etype, value, tb, tb_offset=None, number_of_lines_of_context=5
    ):
        """

        Parameters
        ----------
        etype :
        value :
        tb :
        tb_offset :
        number_of_lines_of_context :

        Returns
        -------

        """
        tb_offset = self.tb_offset if tb_offset is None else tb_offset
        mode = self.mode
        if mode in self.verbose_modes:
            # Verbose modes need a full traceback
            return VerboseTB.structured_traceback(
                self, etype, value, tb, tb_offset, number_of_lines_of_context
            )
        elif mode == "Minimal":
            return ListTB.get_exception_only(self, etype, value)
        else:
            # We must check the source cache because otherwise we can print
            # out-of-date source code.
            self.check_cache()
            # Now we can extract and format the exception
            elist = self._extract_tb(tb)
            return ListTB.structured_traceback(
                self, etype, value, elist, tb_offset, number_of_lines_of_context
            )

    def stb2text(self, stb):
        """Convert a structured traceback (a list) to a string."""
        return self.tb_join_char.join(stb)

    def set_mode(self, mode=None):
        """Switch to the desired mode.

        If mode is not specified, cycles through the available modes.
        """
        if not mode:
            new_idx = (self.valid_modes.index(self.mode) + 1) % len(self.valid_modes)
            self.mode = self.valid_modes[new_idx]
        elif mode not in self.valid_modes:
            raise ValueError(
                "Unrecognized mode in FormattedTB: <" + mode + ">\n"
                "Valid modes: " + str(self.valid_modes)
            )
        else:
            self.mode = mode
        # include variable details only in 'Verbose' mode
        self.include_vars = self.mode == self.valid_modes[2]
        # Set the join character for generating text tracebacks
        self.tb_join_char = self._join_chars[self.mode]

    # some convenient shortcuts
    def plain(self):
        """The implementation of xmode.

        I mean I guess this is a good example of how to do it?
        """
        self.set_mode(self.valid_modes[0])

    def context(self):
        """

        """
        self.set_mode(self.valid_modes[1])

    def verbose(self):
        """

        """
        self.set_mode(self.valid_modes[2])

    def minimal(self):
        """

        """
        self.set_mode(self.valid_modes[3])


class AutoFormattedTB(FormattedTB):
    """A traceback printer which can be called on the fly.

    It will find out about exceptions by itself.

    A brief example::

        AutoTB = AutoFormattedTB(mode='Verbose', color_scheme='Linux')
        try:
            raise
        except:
            AutoTB()  # or AutoTB(out=logfile) where logfile is an open file object

    Methods
    -------
    stb2str
        This method is directly invoked by the
        :class:`~IPython.core.interactiveshell.InteractiveShell` whenever the
        user invokes the :meth:`_showtraceback` method.
        This means that it's invoked, for all intents and purposes, upon every
        :mod:`traceback`.
        As a result it's incredibly important.

        Idk if it's defined in a superclass or something but temporarily I'm
        explicitly defining it here so I can keep track of it.

        I think I found a replacement but I'm not sure. traceback has a function
        called format_list which returns a list of str. Unpack it and we're good?

    Attributes
    -----------
    pdb
        Getting errors because the tests expect a pdb attribute on this class.

    """

    def __init__(
        self,
        mode="Plain",
        color_scheme="Linux",
        call_pdb=False,
        ostream=None,
        tb_offset=0,
        long_header=False,
        include_vars=False,
        check_cache=None,
        debugger_cls=None,
        parent=None,
        config=None,
        *args,
        **kwargs,
    ):
        self.tb = sys.exc_info()
        self.mode = mode
        self.color_scheme = color_scheme
        self.call_pdb = call_pdb
        self.debugger_cls = debugger_cls
        self.long_header = long_header
        self.tb_offset = tb_offset
        self.include_vars = include_vars
        self.ostream = ostream
        self.check_cache = check_cache
        self.Colors = exception_colors()
        self.parent = parent
        self.config = config
        if self.config is None:
            import pdb

            pdb.set_trace()

        super().__init__(
            color_scheme=self.color_scheme,
            call_pdb=self.call_pdb,
            debugger_cls=self.debugger_cls,
            long_header=self.long_header,
            tb_offset=self.tb_offset,
            include_vars=self.include_vars,
            ostream=self.ostream,
            check_cache=self.check_cache,
            parent=self.parent,
            config=self.config,
        )

    def __call__(self, etype=None, evalue=None, etb=None, out=None, tb_offset=None):
        """Print out a formatted exception traceback.

        Optional arguments
        ------------------
        - out: an open file-like object to direct output to.

        - tb_offset: the number of frames to skip over in the stack, on a
          per-call basis (this overrides temporarily the instance's tb_offset
          given at initialization time.

        """
        if out is None:
            out = self.ostream
        out.flush()
        out.write(self.text(etype, evalue, etb, tb_offset))
        out.write("\n")
        out.flush()
        # FIXME: we should remove the auto pdb behavior from here and leave
        # that to the clients.
        try:
            self.debugger()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")

    def structured_traceback(
        self,
        etype=None,
        value=None,
        tb=None,
        tb_offset=None,
        number_of_lines_of_context=5,
    ):
        """

        Parameters
        ----------
        etype :
        value :
        tb :
        tb_offset :
        number_of_lines_of_context :

        Returns
        -------

        """
        if etype is None:
            etype, value, tb = sys.exc_info()
        return FormattedTB.structured_traceback(
            self, etype, value, tb, tb_offset, number_of_lines_of_context
        )

    def stb2text(self, stb):
        """Convert a structured traceback (a list) to a string."""
        return self.tb_join_char.join(stb)


class ColorTB(FormattedTB):
    """Shorthand to initialize a FormattedTB in Linux colors mode."""

    def __init__(self, color_scheme="NoColor", call_pdb=False, **kwargs):
        """Initialize the ColorTB.

        Parameters
        ----------
        color_scheme : object

        Yo we definitely don't call FormattedTB correctly. Here's the init...

            def __init__(
                    self,
                    mode: str = "Plain",
                    color_scheme: object = "Linux",
                    call_pdb: bool = False,
                    ostream: object = None,
                    tb_offset: int = 0,
                    long_header: bool = False,
                    include_vars: bool = False,
                    check_cache: object = None,
                    debugger_cls: object = None,
                    parent: object = None,
                    config: object = None,
            ) -> object:

        """
        self.color_scheme = color_scheme
        self.call_pdb = call_pdb
        FormattedTB.__init__(
            self, call_pdb=self.call_pdb, color_scheme=self.color_scheme, **kwargs
        )
