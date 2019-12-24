==================
Exception Handling
==================

.. module:: exception_handling
   :synopsis: How IPython handles expected and unexpected exceptions.

`ultratb` and :mod:`cgitb`
==========================

.. currentmodule:: IPython.core.ultratb

Verbose and colourful traceback formatting.

**ColorTB**

I've always found it a bit hard to visually parse tracebacks in Python.  The
ColorTB class is a solution to that problem.  It colors the different parts of a
traceback in a manner similar to what you would expect from a syntax-highlighting
text editor.

Installation instructions for ColorTB::

    import sys,ultratb
    sys.excepthook = ultratb.ColorTB()

**VerboseTB**

I've also included a port of Ka-Ping Yee's "cgitb.py" that produces all kinds
of useful info when a traceback occurs.  Ping originally had it spit out HTML
and intended it for CGI programmers, but why should they have all the fun?  I
altered it to spit out colored text to the terminal.  It's a bit overwhelming,
but kind of neat, and maybe useful for long-running programs that you believe
are bug-free.  If a crash *does* occur in that type of program you want details.
Give it a shot--you'll love it or you'll hate it.

.. note::

  The Verbose mode prints the variables currently visible where the exception
  happened (shortening their strings if too long). This can potentially be
  very slow, if you happen to have a huge data structure whose string
  representation is complex to compute. Your computer may appear to freeze for
  a while with cpu usage at 100%. If this occurs, you can cancel the traceback
  with Ctrl-C (maybe hitting it more than once).

  If you encounter this kind of situation often, you may want to use the
  Verbose_novars mode instead of the regular Verbose, which avoids formatting
  variables (but otherwise includes the information and context given by
  Verbose).

.. note::

  The verbose mode print all variables in the stack, which means it can
  potentially leak sensitive information like access keys, or unencrypted
  password.

Installation instructions for VerboseTB::

    import sys,ultratb
    sys.excepthook = ultratb.VerboseTB()

Note:  Much of the code in this module was lifted verbatim from the standard
library module 'traceback.py' and Ka-Ping Yee's 'cgitb.py'.

Color schemes
-------------

The colors are defined in the class TBTools through the use of the
ColorSchemeTable class. Currently the following exist:

  - NoColor: allows all of this module to be used in any terminal (the color
    escapes are just dummy blank strings).

  - Linux: is meant to look good in a terminal like the Linux console (black
    or very dark background).

  - LightBG: similar to Linux but swaps dark/light colors to be more readable
    in light background terminals.

  - Neutral: a neutral color scheme that should be readable on both light and
    dark background

You can implement other color schemes easily, the syntax is fairly
self-explanatory. Please send back new schemes you develop to the author for
possible inclusion in future releases.

.. data:: INDENT_SIZE = 8

    Amount of space to put line numbers before verbose tracebacks.

.. data:: DEFAULT_SCHEME = 'NoColor'

    Default color scheme.  This is used, for example, by the traceback
    formatter.  When running in an actual IPython instance, the user's rc.colors
    value is used, but having a module global makes this functionality available
    to users of ultratb who are NOT running inside IPython.

.. data:: _FRAME_RECURSION_LIMIT = 500

    Number of frame above which we are likely to have a recursion and will
    **attempt** to detect it.  Made modifiable mostly to speedup test suite
    as detecting recursion is one of our slowest tests.


Notes
-----
Even though it seems like a large part of why the module exists,
is there any way to factor out all color considerations?

This is quite a difficult module to work with, so limiting the
responsibliity of the classes to returning formatted tracebacks should
still be plenty of work.

Nov 21, 2019:

As of 2019, most of the patches shown here have been merged upstream to inspect.

As a result, our patches have been removed, saving us from working with ~200
LOC. The remaining module level functions might be able to be deleted.
Still manually inspecting that the patches aren't present upstream.

Dec 02, 2019:

TODO: We'll need to start breaking up the method `structured_traceback`,
a method that'll be particularly difficult to get into smaller pieces as it's
overidden in every subclass that exists in this module.

A good start is implementing 3 methods in every TBTool.:

    def get_etype(self, etype):
        # A closure inside of structured_traceback because we need it's state
        if etype is None:
            self.etype = sys.exc_info[0]
            return self.etype

You can set the return value to etype so that it's locally bound and bound to
the instance.

So that'll hopefully protect us for how insanely inconsistent the
variable handling here is.

Cool. Now we can handle that tuple being None gracefully. Call that method
for each of the 3 components. Check if all 3 are None and if so just bail.

That'll take care of structured_traceback getting called incorrectly and
doesn't provide the traceback info we want; in addition to handling a situation
where it gets called when we didn't have a traceback.


Inheritance diagram:

.. inheritance-diagram:: IPython.core.ultratb
   :parts: 3

"""

# *****************************************************************************
# Copyright (C) 2001 Nathaniel Gray <n8gray@caltech.edu>
# Copyright (C) 2001-2004 Fernando Perez <fperez@colorado.edu>
#
# Distributed under the terms of the BSD License.  The full license is in
# the file COPYING, distributed as part of this software.
# *****************************************************************************
