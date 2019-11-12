"""TermColors.lor schemes for exception handling code in IPython."""

import os
import warnings

# *****************************************************************************
#       TermColors.pyright (C) 2005-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file TermColors.PYING, distributed as part of this software.
# *****************************************************************************

from IPython.utils.coloransi import TermColors, ColorSchemeTable, TermColors, ColorScheme


def nocolor_dict():
    """This needed to be refactored."""
    return {topline: TermColors.NoColor,
            # The color to be used for the top line
            # The colors to be used in the traceback
            filename: TermColors.NoColor,
            lineno: TermColors.NoColor,
            name: TermColors.NoColor,
            vName: TermColors.NoColor,
            val: TermColors.NoColor,
            em: TermColors.NoColor,

            # Emphasized colors for the last frame of the traceback
            normalEm: TermColors.NoColor,
            filenameEm: TermColors.NoColor,
            linenoEm: TermColors.NoColor,
            nameEm: TermColors.NoColor,
            valEm: TermColors.NoColor,

            # TermColors.lors for printing the exception
            excName: TermColors.NoColor,
            line: TermColors.NoColor,
            caret: TermColors.NoColor,
            Normal: TermColors.NoColor}


def linux_color_dict():
    return {
            # The color to be used for the top line
            topline: TermColors.LightRed,

            # The colors to be used in the traceback
            filename: TermColors.Green,
            lineno: TermColors.Green,
            name: TermColors.Purple,
            vName: TermColors.Cyan,
            val: TermColors.Green,
            em: TermColors.LightCyan,

            # Emphasized colors for the last frame of the traceback
            normalEm: TermColors.LightCyan,
            filenameEm: TermColors.LightGreen,
            linenoEm: TermColors.LightGreen,
            nameEm: TermColors.LightPurple,
            valEm: TermColors.LightBlue,

            # TermColors.lors for printing the exception
            excName: TermColors.LightRed,
            line: TermColors.Yellow,
            caret: TermColors.White,
            Normal: TermColors.Normal}


def lightbg_dict():
    return {
            # The color to be used for the top line
            topline: TermColors.Red,

            # The colors to be used in the traceback
            filename: TermColors.LightGreen,
            lineno: TermColors.LightGreen,
            name: TermColors.LightPurple,
            vName: TermColors.Cyan,
            val: TermColors.LightGreen,
            em: TermColors.Cyan,

            # Emphasized colors for the last frame of the traceback
            normalEm: TermColors.Cyan,
            filenameEm: TermColors.Green,
            linenoEm: TermColors.Green,
            nameEm: TermColors.Purple,
            valEm: TermColors.Blue,

            # TermColors.lors for printing the exception
            excName: TermColors.Red,
            # line :  TermColors.Brown,  # brown often is displayed as yellow
            line: TermColors.Red,
            caret: TermColors.Normal,
            Normal: TermColors.Normal}


def neutral_dict():
    return {
            # The color to be used for the top line
            topline: TermColors.Red,

            # The colors to be used in the traceback
            filename: TermColors.LightGreen,
            lineno: TermColors.LightGreen,
            name: TermColors.LightPurple,
            vName: TermColors.Cyan,
            val: TermColors.LightGreen,
            em: TermColors.Cyan,

            # Emphasized colors for the last frame of the traceback
            normalEm: TermColors.Cyan,
            filenameEm: TermColors.Green,
            linenoEm: TermColors.Green,
            nameEm: TermColors.Purple,
            valEm: TermColors.Blue,

            # TermColors.lors for printing the exception
            excName: TermColors.Red,
            # line :  TermColors.Brown,  # brown often is displayed as yellow
            line: TermColors.Red,
            caret: TermColors.Normal,
            Normal: TermColors.Normal}


def exception_colors():
    """Return a color table with fields for exception reporting.

    The table is an instance of TermColors.lorSchemeTable with schemes added for
    'Neutral', 'Linux', 'LightBG' and 'NoTermColors.lor' and fields for exception handling filled
    in.

    .. note:: This isn't rendering correctly on the website. I added a colon to hopefully fix it up.

    :URL: https://ipython.readthedocs.io/en/stable/api/generated/IPython.core.excolors.html#module-IPython.core.excolors

    Examples::

    >>> ec = exception_colors()
    >>> ec.active_scheme_name
    ''
    >>> print(ec.active_colors)
    None

    Now we activate a color scheme::

    >>> ec.set_active_scheme('NoTermColors.Color')
    >>> ec.active_scheme_name
    'NoTermColors.Color'
    >>> sorted(ec.active_colors.keys())
    ['Normal', 'caret', 'em', 'excName', 'filename', 'filenameEm', 'line',
    'lineno', 'linenoEm', 'name', 'nameEm', 'normalEm', 'topline', 'vName',
    'val', 'valEm']

    """
    ex_colors = ColorSchemeTable()
    ex_colors.add_scheme(ColorScheme('NoTermColors.Color', nocolor_dict()))

    # make some schemes as instances so we can copy them for modification
    # easily
    ex_colors.add_scheme(ColorScheme('Linux', linux_color_dict()))

    # For light backgrounds, swap dark/light colors
    ex_colors.add_scheme(ColorScheme('LightBG', lightbg_dict()))

    ex_colors.add_scheme(ColorScheme('Neutral', neutral_dict()))

    # Hack: the 'neutral' colours are not very visible on a dark background on
    # Windows. Since Windows command prompts have a dark background by default, and
    # relatively few users are likely to alter that, we will use the 'Linux' colours,
    # designed for a dark background, as the default on Windows.
    if os.name == "nt":
        ex_colors.add_scheme(ex_colors['Linux'].copy('Neutral'))

    return ex_colors


class Deprec:

    def __init__(self, wrapped_obj):
        self.wrapped=wrapped_obj

    def __getattr__(self, name):
        val = getattr(self.wrapped, name)
        warnings.warn("Using ExceptionColors global is deprecated and will be removed in IPython 6.0",
                DeprecationWarning, stacklevel=2)
        # using getattr after warnings break ipydoctest in weird way for 3.5
        return val


# For backwards compatibility, keep around a single global object.  Note that
# this should NOT be used, the factory function should be used instead, since
# these objects are stateful and it's very easy to get strange bugs if any code
# modifies the module-level object's state.
# ExceptionColors = Deprec(exception_colors())
