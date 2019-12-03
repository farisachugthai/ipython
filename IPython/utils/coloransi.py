"""Tools for coloring text in ANSI terminals.

Featured Below:

Default Dark scheme by Chris Kempson (http://chriskempson.com)

"""

# *****************************************************************************
#       Copyright (C) 2002-2006 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************

# As a better way to subclass Dict
from collections import defaultdict
import copy
import os

from IPython.utils.ipstruct import Struct
from pygments.style import Style
from pygments.token import (Keyword, Name, Comment, String, Error, Text,
                            Number, Operator, Literal, Token)
# TODO:
# from pygments import highlight
# from pygments.console import ansiformat

color_templates = (
    # Dark colors
    ("Black", "0;30"),
    ("Red", "0;31"),
    ("Green", "0;32"),
    ("Brown", "0;33"),
    ("Blue", "0;34"),
    ("Purple", "0;35"),
    ("Cyan", "0;36"),
    ("LightGray", "0;37"),
    # Light colors
    ("DarkGray", "1;30"),
    ("LightRed", "1;31"),
    ("LightGreen", "1;32"),
    ("Yellow", "1;33"),
    ("LightBlue", "1;34"),
    ("LightPurple", "1;35"),
    ("LightCyan", "1;36"),
    ("White", "1;37"),
    # Blinking colors.  Probably should not be used in anything serious.
    ("BlinkBlack", "5;30"),
    ("BlinkRed", "5;31"),
    ("BlinkGreen", "5;32"),
    ("BlinkYellow", "5;33"),
    ("BlinkBlue", "5;34"),
    ("BlinkPurple", "5;35"),
    ("BlinkCyan", "5;36"),
    ("BlinkLightGray", "5;37"),
)


def make_color_table(in_class):
    """Build a set of color attributes in a class.

    Helper function for building the :class:`TermColors` and
    :class`InputTermColors`.
    """
    for name, value in color_templates:
        setattr(in_class, name, in_class._base % value)


class TermColors:
    """Color escape sequences.

    This class defines the escape sequences for all the standard (ANSI?)
    colors in terminals. Also defines a NoColor escape which is just the null
    string, suitable for defining 'dummy' color schemes in terminals which get
    confused by color escapes.

    This class should be used as a mixin for building color schemes."""

    NoColor = ''  # for color schemes in color-less terminals.
    Normal = '\033[0m'  # Reset normal coloring
    _base = '\033[%sm'  # Template for all other colors


# Build the actual color table as a set of class attributes:
make_color_table(TermColors)


class InputTermColors:
    """Color escape sequences for input prompts.

    This class is similar to TermColors, but the escapes are wrapped in \001
    and \002 so that readline can properly know the length of each line and
    can wrap lines accordingly.  Use this class for any colored text which
    needs to be used in input prompts, such as in calls to raw_input().

    This class defines the escape sequences for all the standard (ANSI?)
    colors in terminals. Also defines a NoColor escape which is just the null
    string, suitable for defining 'dummy' color schemes in terminals which get
    confused by color escapes.

    This class should be used as a mixin for building color schemes."""

    NoColor = ''  # for color schemes in color-less terminals.

    if os.name == 'nt' and os.environ.get('TERM', 'dumb') == 'emacs':
        # (X)emacs on W32 gets confused with \001 and \002 so we remove them
        Normal = '\033[0m'  # Reset normal coloring
        _base = '\033[%sm'  # Template for all other colors
    else:
        Normal = '\001\033[0m\002'  # Reset normal coloring
        _base = '\001\033[%sm\002'  # Template for all other colors


# Build the actual color table as a set of class attributes:
make_color_table(InputTermColors)


class NoColors:
    """This defines all the same names as the colour classes, but maps them to
    empty strings, so it can easily be substituted to turn off colours."""
    NoColor = ''
    Normal = ''


for name, value in color_templates:
    setattr(NoColors, name, '')


class ColorScheme:
    """Generic color scheme class. Just a name and a Struct."""

    def __init__(self, name, colordict=None, **colormap) -> object:
        """

        Returns
        -------
        dict-like object
        """
        self.name = name
        if colordict is None:
            self.colors = Struct(**colormap)
        else:
            self.colors = Struct(colordict)

    def copy(self, name=None):
        """Return a full copy of the object, optionally renaming it.

        Isnt there a dunder method for this that maybe is a better idea to use?
        """
        if name:
            self.name = name
        return ColorScheme(self.name, self.colors.dict())

    def __copy__(self):
        return copy.copy(self.copy())


class ColorSchemeTable(dict):
    """General class to handle tables of color schemes.

    It's basically a dict of color schemes with a couple of shorthand
    attributes and some convenient methods.

    active_scheme_name -> obvious
    active_colors -> actual color table of the active scheme

    """

    def __init__(self, scheme_list=None, default_scheme=None):
        """Create a table of color schemes.

        The table can be created empty and manually filled or it can be
        created with a list of valid color schemes AND the specification for
        the default active scheme.

        Yo this is outrageously confusing. self.active_scheme_name is treated
        like the default_scheme parameter.

        scheme_list is a list of dicts.

        we never bind the valid_schemes to the instance.

j        """
        # Yo pycharm recommended we add this...does it do anything?
        super().__init__()
        valid_schemes = ['linux', 'lightbg', 'nocolor', 'neutral']
        self.valid_schemes = valid_schemes
        # create object attributes to be set later
        self.active_scheme_name = ''
        self.active_colors = None

        if scheme_list:
            self.scheme_list = scheme_list
        else:
            self.scheme_list = valid_schemes

        if default_scheme is None:
            self.active_scheme_name = 'LightBG'
        else:
            self.active_scheme_name = default_scheme

        for scheme in self.scheme_list:
            self.add_scheme(scheme)
        # self.set_active_scheme(default_scheme)

        self.scheme_names = list(self.keys())

        if self.scheme_names is not None:
            self.valid_schemes = [s.lower() for s in self.scheme_names if isinstance(s, str)]
        else:
            self.scheme_names = ['linux', 'lightbg', 'nocolor', 'iforgetrn']

    def copy(self):
        """Return full copy of object"""
        return ColorSchemeTable(self.values(), self.active_scheme_name)

    def __copy__(self):
        """Seriously can we not just make these dunders?"""
        return copy.copy(self.values())

    def add_scheme(self, new_scheme):
        """Add a new color scheme to the table."""
        # if not isinstance(new_scheme, ColorScheme):
        # raise ValueError(
        #     'ColorSchemeTable only accepts ColorScheme instances')
        if isinstance(new_scheme, dict):
            # let's just do the work ourselves stop raising errors
            new_scheme = ColorScheme('tmp_name', new_scheme)
        if isinstance(new_scheme, str):
            # raise TypeError('We got a str when expecting a ColorScheme object')
            if new_scheme in self.valid_schemes:
                return
        self[new_scheme.name] = new_scheme

    def __add__(self, new_scheme):
        return self.add_scheme(new_scheme)

    def set_active_scheme(self, scheme):
        """Set the currently active scheme.

        Names are by default compared in a case-insensitive way, but this can
        be changed by setting the parameter case_sensitive to true.

        case sensitive now ignored.
        """
        raise NotImplementedError('fuck it')
        # try:
        # scheme_idx = self.valid_schemes.index(scheme_test)
        # Seriously why the fuck does this use THIS many different variables
        # scheme
        # scheme_list
        # scheme_test
        # scheme_names
        # valid_schemes
        # active_scheme_name,
        # active_colors
        # Colors
        # self.values
        # valid_schemes
        # active
        # scheme_idx

        # IT ALL REPRESENTS ONE OBJECT.
        # THIS ISN'T THE HARD PART
        # except ValueError:
        #     raise ValueError('Unrecognized color scheme: ' + scheme +
        #                      '\nValid schemes: ' + str(self.scheme_names).replace("'', ", ''))
        # else:
        #     active = self.scheme_names[scheme_idx]
        #     self.active_scheme_name = active
        #     self.active_colors = self[active].colors
        #     # Now allow using '' as an index for the current active scheme
        #     self[''] = self[active]


class DefaultDark(defaultdict):
    """Rewriting the ColorSchemeTable.

    See http://chriskempson.com/projects/base16/ for a description of the role
    of the different colors in the base16 palette.

    .. todo:: This raises

    TypeError: Can't instantiate abstract class DefaultDark with abstract methods __delitem__, __getitem__, __iter__, __len__, __setitem__

    """

    def __init__(self):
        super(DefaultDark, self).__init__()
        self.color_scheme = ColorScheme('default_dark', colordict={
            'base00': '#181818',
            'base01': '#282828',
            'base02': '#383838',
            'base03': '#585858',
            'base04': '#b8b8b8',
            'base05': '#d8d8d8',
            'base06': '#e8e8e8',
            'base07': '#f8f8f8',
            'base08': '#ab4642',
            'base09': '#dc9656',
            'base0A': '#f7ca88',
            'base0B': '#a1b56c',
            'base0C': '#86c1b9',
            'base0D': '#7cafc2',
            'base0E': '#ba8baf',
            'base0F': '#a16946',
        })

    @property
    def colors(self):
        """Should be a property as we shouldn't be able to assign to this."""
        return self.color_scheme


class Base16Style(defaultdict):
    """I feel like I did this really wrong."""
    # See http://pygments.org/docs/tokens/ for a description of the different
    # pygments tokens.
    background_color = "base00"
    highlight_color = "base02"
    default_style = "base05"

    styles = {
        Text: "base05",
        Error: '%s bold' % "base08",
        Comment: "base03",
        Keyword: "base0E",
        Keyword.Constant: "base09",
        Keyword.Namespace: "base0D",
        Name.Builtin: "base0D",
        Name.Function: "base0D",
        Name.Class: "base0D",
        Name.Decorator: "base0E",
        Name.Exception: "base08",
        Number: "base09",
        Operator: "base0E",
        Literal: "base0B",
        String: "base0B",
    }

    @property
    def colors(self):
        return styles

    # See https://github.com/jonathanslenders/python-prompt-toolkit/blob/master/prompt_toolkit/styles/defaults.py
    # for a description of prompt_toolkit related pseudo-tokens.

    overrides = {
        Token.Prompt: "base0B",
        Token.PromptNum: '%s bold' % "base0B",
        Token.OutPrompt: "base08",
        Token.OutPromptNum: '%s bold' % "base08",
        Token.Menu.Completions.Completion: 'bg:%s %s' % ("base01", "base04"),
        Token.Menu.Completions.Completion.Current: 'bg:%s %s' % ("base04", "base01"),
        Token.MatchingBracket.Other: 'bg:%s %s' % ("base03", "base00")
    }
