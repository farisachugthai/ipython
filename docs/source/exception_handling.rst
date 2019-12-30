==================
Exception Handling
==================

.. module:: exception_handling
   :synopsis: How IPython handles expected and unexpected exceptions.

`ultratb` and :mod:`cgitb`
==========================

.. currentmodule:: IPython.core.ultratb

Verbose and colourful traceback formatting.

.. class:: ColorTB

   I've always found it a bit hard to visually parse tracebacks in Python.  The
   ColorTB class is a solution to that problem.  It colors the different parts of a
   traceback in a manner similar to what you would expect from a syntax-highlighting
   text editor.

Installation instructions for `ColorTB`::

    import sys,ultratb
    sys.excepthook = ultratb.ColorTB()

.. class:: VerboseTB

   I've also included a port of Ka-Ping Yee's "cgitb.py" that produces all kinds
   of useful info when a traceback occurs.  Ping originally had it spit out HTML
   and intended it for CGI programmers, but why should they have all the fun?  I
   altered it to spit out colored text to the terminal.  It's a bit overwhelming,
   but kind of neat, and maybe useful for long-running programs that you believe
   are bug-free.  If a crash *does* occur in that type of program you want details.
   Give it a shot--you'll love it or you'll hate it.

.. note:: On Using VerboseTB

  The Verbose mode prints the variables currently visible where the exception
  happened (shortening their strings if too long).

This can potentially be very slow, if you happen to have a huge data
structure whose string representation is complex to compute.

Your computer may appear to freeze for a while with cpu usage at 100%.
If this occurs, you can cancel the traceback with Ctrl-C
(maybe hitting it more than once).

If you encounter this kind of situation often, you may want to use the
Verbose_novars mode instead of the regular Verbose, which avoids formatting
variables (but otherwise includes the information and context given by
Verbose).

.. note::

  The verbose mode print all variables in the stack, which means it can
  potentially leak sensitive information like access keys, or unencrypted
  password.

Installation instructions for `VerboseTB`::

    import sys,ultratb
    sys.excepthook = ultratb.VerboseTB()

Note:  Much of the code in this module was lifted verbatim from the standard
library module 'traceback.py' and Ka-Ping Yee's 'cgitb.py'.

Color schemes
-------------

The colors are defined in the class `TBTools` through the use of the
:class:`~IPython.utils.coloransi.ColorSchemeTable` class.

Currently the following exist:

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
responsibility of the classes to returning formatted tracebacks should
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

A good start is implementing 3 methods in every TBTool.::

    def get_etype(self, etype):
        # A closure inside of structured_traceback because we need it's state
        if etype is None:
            self.etype = sys.exc_info[0]
            return self.etype

You can set the return value to 'etype' so that it's locally bound and bound to
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


Exception Handling in the `InteractiveShell`
============================================

.. currentmodule:: IPython.core.interactiveshell

Custom Exception Handlers
-------------------------

More of a todo for the moment.

.. function:: InteractiveShell.set_custom_exc(exc_tuple, handler)

   Set a handler if self.run_code() raises an error.

   Set a custom exception handler, which will be called if any of the
   exceptions in 'exc_tuple' occur in the mainloop (specifically, in the
   run_code() method).

   Parameters
   ----------
   exc_tuple : tuple
      A *tuple* of exception classes, for which to call the defined
      handler.  It is very important that you use a tuple, and NOT A
      LIST here, because of the way Python's except statement works.  If
      you only want to trap a single exception, use a singleton tuple:

         exc_tuple == (MyCustomException,)

   handler : callable
      'handler' must have the following signature.::

          def my_handler(self, etype, value, tb, tb_offset=None):
              ...
              return structured_traceback

      Your handler must return a structured traceback (a list of strings), or None.
      This will be made into an instance method (via types.MethodType)
      of IPython itself, and it will be called if any of the exceptions
      listed in the exc_tuple are caught. If the handler is None, an
      internal basic one is used, which just prints basic info.

      To protect IPython from crashes, if your handler ever raises an
      exception or returns an invalid result, it will be immediately
      disabled.

      This facility should only be used if you really know what you are doing.

   Raises
   ------
   :exc:`TypeError`
      If 'exc_tuple' is not a `tuple`.

It should absolutely be noted that 'exc_tuple' passes through the
method untouched. We simply assign it to the instance's 'custom_exceptions'
attribute.

If it's **THAT** important to make sure it's a list then validate it.

But handling the 'CustomTB' attribute and the 'custom_exceptions' attribute
feels like 2 separate problems and should be 2 different methods.

We assign to CustomTB to define an exception handler. Then we can separately
define what exceptions it catches, and that feels easier to test and validate
then having a method with 3 nested closures inside of it.

With that much state why not just make a new mixin?

Also the explanation for what the 'exc_tuple' and 'handler' mean to the
`set_custom_exc` function should not be:

   Set a handler if self.run_code() raises an error.

Does it matter what kind of errors? User defined or system? Warnings don't
count do they? Well I guess it depends on what kind of handlers? How they
handle the Exception, *I'm guessing*, is divvied up between.:

   * Be noisy and annoy the user
   * Do nothing which is pointless
   * Crash the program which NO
   * Allow the user to step through and figure out what happened. But that's
     a debugger.

Like I can surmise that `set_custom_exc` takes a handler to handle an
exception. That's borderline tautology.

The only reason I'm writing all this is because for all the documentation
and source code I've read, I genuinely don't know how to interface with
this section of the code.

Actually we kinda need to make a separate method for custom exceptions.

.. code-block:: ipythontb

   Traceback (most recent call last):
   File "/mnt/c/Users/faris/src/ipython/IPython/core/interactiveshell/__init__.py", line 3540, in run_ast_nodes
      if await self.run_code(code, result, async_=asy):
   File "/mnt/c/Users/faris/src/ipython/IPython/core/interactiveshell/__init__.py", line 3620, in run_code
      except self.custom_exceptions:
   TypeError: catching classes that do not inherit from BaseException is not allowed

So we need to validate that 'custom_exceptions' attribute that we assign to
in 'set_custom_exc'.
