.. _reference:

=================
IPython Reference
=================

.. module:: reference
    :synopsis: Reference materials for IPython.

.. highlight:: ipython

.. _command_line_options:

Command-line usage
==================

You start IPython with the command:

.. program:: ipython [options] [-c <statement>] [-m <module>]

If invoked with one or more files passed as arguments,
the shell executes all the files listed in sequence and exits.
The shell can remain in interactive mode with the `-i` flag however.

.. option:: -i, --interactive [<file to execute>]

   Execute a file, then enter the interactive interpreter while still
   recognizing and executing any default options  set in  ``ipython_config.py``.

This behavior is different from standard Python, which when called as::

   python -i [file]

will execute only that one file, and in doing so, will ignore your
configuration setup.

Please note that some of the configuration options are not available at the
command line, simply because they are not practical there. Look into your
configuration files for details on those. There are separate configuration files
for each profile, and the files look like ``ipython_config.py`` or
``ipython_config_{frontendname}.py``.

Profile directories look like ``profile_{profilename}`` and are
typically installed in the :envvar:`IPYTHONDIR` directory, which defaults
to ``$HOME/.ipython`` or ``%USERPROFILE%\.ipython``.


Command-line Options
--------------------

To see the options IPython accepts before startup, run ``ipython --help``.
For more verbose output, consider running ``ipython --help-all``.

.. admonition:: To use the %page magic, ensure that the $PAGER env var is set.

   This variable is set by default on Unix-like systems where rendering text
   in a terminal is more common; however, it typically is not set on Windows.


Help all
--------

This shows all the options that IPython accepts, in addition to flags that
have a single-word alias to toggle them. IPython lets a user configure all of
it's objects from the command-line by passing the full class name and a
corresponding value.

As an example, type ``ipython --help-all`` to see this full list.::

   $ ipython --help-all

   <...SNIP...>

   --matplotlib=<CaselessStrEnum> (InteractiveShellApp.matplotlib)
      Default: None
      Choices: ['auto', 'gtk', 'gtk3', 'inline', 'nbagg', 'notebook', 'osx', 'qt', 'qt4', 'qt5', 'tk', 'wx']
      Configure matplotlib for interactive use with the default matplotlib
      backend.

   <...SNIP...>


Indicates that the following::

   $ ipython --matplotlib qt


is equivalent to::

   $ ipython --TerminalIPythonApp.matplotlib='qt'

.. tip:: Run the output through a pager such as ``ipython --help-all | less`` for more convenient reading.

Note that in the second form, you *must* use the equal sign, as the expression
is evaluated as an actual Python assignment.

While in the above example the short form is more convenient,
only the most common options have a short form,
while any configurable variable in IPython can be set at the command-line by
using the long form.  This long form is the same syntax used in the
configuration files, if you want to set these options permanently.


IPython as your default Python environment
==========================================

Python honors the environment variable :envvar:`PYTHONSTARTUP` and will
execute at startup the file referenced by this variable. If you put the
following code at the end of that file, then IPython will be your working
environment anytime you start Python::

    import os, IPython
    os.environ['PYTHONSTARTUP'] = ''  # Prevent running this again
    IPython.start_ipython()
    raise SystemExit

The ``raise SystemExit`` is needed to exit Python when
it finishes, otherwise you'll be back at the normal Python ``>>>``
prompt.

This is probably useful to developers who manage multiple Python
versions and don't want to have correspondingly multiple IPython
versions. Note that in this mode, there is no way to pass IPython any
command-line options, as those are trapped first by Python itself.

.. _Embedding:

Embedding IPython
=================

You can start a regular IPython session with

.. sourcecode:: python

    import IPython
    IPython.start_ipython(argv=[])

at any point in your program.  This will load IPython configuration,
startup files, and everything, just as if it were a normal IPython session.
For information on setting configuration options when running IPython from
python, see :ref:`configure_start_ipython`.

It is also possible to embed an IPython shell in a namespace in your Python
code. This allows you to evaluate dynamically the state of your code, operate
with your variables, analyze them, etc. For example, if you run the following
code snippet::

  import IPython

  a = 42
  IPython.embed()

and within the IPython shell, you reassign `a` to `23` to do further testing of
some sort, you can then exit::

  >>> IPython.embed()
  Python 3.6.2 (default, Jul 17 2017, 16:44:45)
  Type 'copyright', 'credits' or 'license' for more information
  IPython 6.2.0.dev -- An enhanced Interactive Python. Type '?' for help.

  In [1]: a = 23

  In [2]: exit()

Once you exit and print `a`, the value 23 will be shown::

  In: print(a)
  23

It's important to note that the code run in the embedded IPython shell will
*not* change the state of your code and variables, **unless** the shell is
contained within the global namespace. In the above example, `a` is changed
because this is true.

To further exemplify this, consider the following example::

  import IPython
  def do():
      a = 42
      print(a)
      IPython.embed()
      print(a)

Now if one calls the function and complete the state changes as we did above, the
value `42` will be printed. Again, this is because it's not in the global
namespace::

  do()

Running a file with the above code can lead to the following session::

  >>> do()
  42
  Python 3.6.2 (default, Jul 17 2017, 16:44:45)
  Type 'copyright', 'credits' or 'license' for more information
  IPython 6.2.0.dev -- An enhanced Interactive Python. Type '?' for help.

  In [1]: a = 23

  In [2]: exit()
  42

.. note::

  At present, embedding IPython cannot be done from inside IPython.
  Run the code samples below outside IPython.

This feature allows you to easily have a fully functional python
environment for doing object introspection anywhere in your code with a
simple function call. In some cases a simple print statement is enough,
but if you need to do more detailed analysis of a code fragment this
feature can be very valuable.

It can also be useful in scientific computing situations where it is
common to need to do some automatic, computationally intensive part and
then stop to look at data, plots, etc.

Opening an IPython instance will give you full access to your data and
functions, and you can resume program execution once you are done with
the interactive part (perhaps to stop again later, as many times as
needed).

The following code snippet is the bare minimum you need to include in
your Python programs for this to work (detailed examples follow later)::

    from IPython import embed

    embed() # this call anywhere in your program will start IPython

You can also embed an IPython *kernel*, for use with qtconsole, etc. via
``IPython.embed_kernel()``. This should work the same way, but you can
connect an external frontend (``ipython qtconsole`` or ``ipython console``),
rather than interacting with it in the terminal.

You can run embedded instances even in code which is itself being run at
the IPython interactive prompt with '%run <filename>'. Since it's easy
to get lost as to where you are (in your top-level IPython or in your
embedded one), it's a good idea in such cases to set the in/out prompts
to something different for the embedded instances. The code examples
below illustrate this.

You can also have multiple IPython instances in your program and open
them separately, for example with different options for data
presentation. If you close and open the same instance multiple times,
its prompt counters simply continue from each execution to the next.

.. whoa. that file hasn't existed in a while.

Please look at the docstrings in the :mod:`~IPython.terminal.embed`
module for more details on the use of this system.

The following sample file illustrating how to use the embedding
functionality is provided in the examples directory as
:file:`../../examples/Embedding/embed_class_long.py`_.
It should be fairly self-explanatory:

 .. literalinclude:: /../../examples/Embedding/embed_class_long.py
     :language: python

Once you understand how the system functions, you can use the following
code fragments in your programs which are ready for cut and paste:

 .. literalinclude:: ../../examples/Embedding/embed_class_short.py
     :language: python


Using the Python debugger (pdb)
===============================

:mod:`pdb`, the Python debugger, is a powerful interactive debugger which
allows you to step through code, set breakpoints, watch variables,
etc.  IPython makes it very easy to start any script under the control
of pdb, regardless of whether you have wrapped it into a 'main()'
function or not. For this, simply type ``%run -d myscript`` at an
IPython prompt. See the :magic:`run` command's documentation for more details, including
how to control where pdb will stop execution first.

.. _debugger-see-also:

See Also
--------

For more information on the use of the pdb debugger, see :ref:`debugger-commands`
in the Python documentation.

For IPython specific API information, see :mod:`IPython.core.debugger` and
:mod:`IPython.terminal.debugger`.

Running entire programs via pdb
-------------------------------

IPython extends the debugger with a few useful additions, like coloring of
tracebacks. The debugger will adopt the color scheme selected for IPython.

The ``where`` command has also been extended to take as argument the number of
context line to show. This allows to a many line of context on shallow stack trace:

.. sourcecode:: ipython

    In [5]: def foo(x):
    ...:     1
    ...:     2
    ...:     3
    ...:     return 1/x+foo(x-1)
    ...:     5
    ...:     6
    ...:     7
    ...:

    In[6]: foo(1)
    # ...
    ipdb> where 8
    <ipython-input-6-9e45007b2b59>(1)<module>
    ----> 1 foo(1)

    <ipython-input-5-7baadc3d1465>(5)foo()
        1 def foo(x):
        2     1
        3     2
        4     3
    ----> 5     return 1/x+foo(x-1)
        6     5
        7     6
        8     7

    > <ipython-input-5-7baadc3d1465>(5)foo()
        1 def foo(x):
        2     1
        3     2
        4     3
    ----> 5     return 1/x+foo(x-1)
        6     5
        7     6
        8     7


And less context on shallower Stack Trace:

.. code:: ipython

    ipdb> where 1
    <ipython-input-13-afa180a57233>(1)<module>
    ----> 1 foo(7)

    <ipython-input-5-7baadc3d1465>(5)foo()
    ----> 5     return 1/x+foo(x-1)

    <ipython-input-5-7baadc3d1465>(5)foo()
    ----> 5     return 1/x+foo(x-1)

    <ipython-input-5-7baadc3d1465>(5)foo()
    ----> 5     return 1/x+foo(x-1)

    <ipython-input-5-7baadc3d1465>(5)foo()
    ----> 5     return 1/x+foo(x-1)


Post-mortem debugging
---------------------

.. option:: --pdb

   Enable the IPython-enhanced debugger if any code executed in the session
   triggers an uncaught exception.

Going into a debugger when an exception occurs can be
extremely useful in order to find the origin of subtle bugs, because pdb
opens up at the point in your code which triggered the exception, and
while your program is at this point 'dead', all the data is still
available and you can walk up and down the stack frame and understand
the origin of the problem.

You can use the :magic:`debug` magic after an exception has occurred to start
post-mortem debugging. IPython can also call debugger every time your code
triggers an uncaught exception. This feature can be toggled with the :magic:`pdb` magic
command, or you can start IPython with the ``--pdb`` option.

.. For a post-mortem debugger in your programs outside IPython,
.. put the following lines toward the top of your 'main' routine::

..     import sys
..     from IPython.core import ultratb
..     sys.excepthook = ultratb.FormattedTB(mode='Verbose',
..     color_scheme='Linux', call_pdb=1)


.. option:: --xmode

   The 'mode' keyword can be either 'Verbose' or 'Plain', giving either very
   detailed or normal tracebacks respectively.

.. option:: --colors

   The 'color_scheme' keyword can be one of 'NoColor', 'Linux' (default) or
   'LightBG'.


This will give any of your programs detailed, colored tracebacks with
automatic invocation of :mod:`pdb`.


.. _pasting_with_prompts:

Pasting of code starting with Python or IPython prompts
=======================================================

IPython is smart enough to filter out input prompts, be they plain Python ones
(``>>>`` and ``...``) or IPython ones (``In [N]:`` and ``...:``).  You can
therefore copy and paste from existing interactive sessions without worry.

The following is a 'screenshot' of how things work, copying an example from the
standard Python tutorial::

    In [1]: >>> # Fibonacci series:

    In [2]: ... # the sum of two elements defines the next

    In [3]: ... a, b = 0, 1

    In [4]: >>> while b < 10:
       ...:     ...     print(b)
       ...:     ...     a, b = b, a+b
       ...:
    1
    1
    2
    3
    5
    8

And pasting from IPython sessions works equally well::

    In [1]: In [5]: def f(x):
       ...:        ...:     "A simple function"
       ...:        ...:     return x**2
       ...:    ...:

    In [2]: f(3)
    Out[2]: 9


In addition, interactive sessions can be copy-pasted and placed into
documentation as per the Sphinx extension. See more :ref:`ipython-directive`.


.. _gui_support:

GUI event loop support
======================

.. magic:: gui

IPython has excellent support for working interactively with Graphical User
Interface (GUI) toolkits, such as wxPython, PyQt4/PySide, PyGTK and Tk. This is
implemented by running the GUI's front end event loop while IPython waits for input.

For users, enabling GUI event loop integration is simple.  You simple use the
:magic:`gui` magic as follows::

    %gui [GUINAME]

With no arguments, `%gui` removes all GUI support.  Valid
arguments include ``wx``, ``qt``, ``qt4``, ``qt5``, ``gtk``, ``gtk3`` and ``tk``.

In addition, ``glut``, ``gtk2``, ``osx``, and ``pyglet`` are also acceptable flags.

.. versionchanged:: 7.10.0

   asyncio is now a valid flag

Thus, to use wxPython interactively and create a running :class:`wx.App`
object, enter the following in the REPL.::

    %gui wx

You can also start IPython with an event loop set up using the `--gui`
flag on the command line.::

    $ ipython --gui=qt

For information on IPython's `matplotlib` integration (and the `matplotlib`
mode) see :ref:`more on IPython's matplotlib support <matplotlib_support>`.

For developers that want to integrate additional event loops with IPython, see
:doc:`eventloops`.

When running inside IPython with an integrated event loop, a GUI application
should *not* start its own event loop.

This means that applications that are meant to be used both
in IPython and as standalone apps need to have special code to detect how the
application is being run.

We highly recommend using IPython's support for this.

Since the details vary slightly between toolkits, we point you to the various
examples in our source directory :doc:`../../examples/IPython Kernel/gui/` that
demonstrate these capabilities.

PyQt and PySide
---------------

.. attempt at explanation of the complete mess that is Qt support

.. option:: --gui[=asyncio,qt,qt4,qt5,wx,macOS,gtk,gtk2,gtk3

When you use ``--gui=qt`` or ``--matplotlib=qt``, IPython can work with either
PyQt4 or PySide.  There are three options for configuration here, because
PyQt4 has two APIs for QString and QVariant: v1, which is the default on
Python 2, and the more natural v2, which is the only API supported by PySide.
v2 is also the default for PyQt4 on Python 3.  IPython's code for the QtConsole
uses v2, but you can still use any interface in your code, since the
Qt frontend is in a different process.

The default will be to import PyQt4 without configuration of the APIs, thus
matching what most applications would expect. It will fall back to PySide if
PyQt4 is unavailable.

If specified, IPython will respect the environment variable ``QT_API`` used
by ETS.  ETS 4.0 also works with both PyQt4 and PySide, but it requires
PyQt4 to use its v2 API.  So if ``QT_API=pyside`` PySide will be used,
and if ``QT_API=pyqt`` then PyQt4 will be used *with the v2 API* for
QString and QVariant, so ETS codes like MayaVi will also work with IPython.

If you launch IPython in matplotlib mode with ``ipython --matplotlib=qt``,
then IPython will ask matplotlib which Qt library to use (only if QT_API is
*not set*), via the 'backend.qt4' rcParam.  If matplotlib is version 1.0.1 or
older, then IPython will always use PyQt4 without setting the v2 APIs, since
neither v2 PyQt nor PySide work.

.. warning::

    Note that this means for ETS 4 to work with PyQt4, ``QT_API`` *must* be set
    to work with IPython's qt integration, because otherwise PyQt4 will be
    loaded in an incompatible mode.

    It also means that you must *not* have ``QT_API`` set if you want to
    use ``--gui=qt`` with code that requires PyQt4 API v1.



Support for creating GUI apps and starting event loops.
-------------------------------------------------------
.. the old docstring from lib.guisupport

IPython's GUI integration allows interactive plotting and GUI usage in IPython
session. IPython has two different types of GUI integration:

1. The terminal based IPython supports GUI event loops through Python's
   PyOS_InputHook. PyOS_InputHook is a hook that Python calls periodically
   whenever raw_input is waiting for a user to type code. We implement GUI
   support in the terminal by setting PyOS_InputHook to a function that
   iterates the event loop for a short while. It is important to note that
   in this situation, the real GUI event loop is NOT run in the normal
   manner, so you can't use the normal means to detect that it is running.
2. In the two process IPython kernel/frontend, the GUI event loop is run in
   the kernel. In this case, the event loop is run in the normal manner by
   calling the function or method of the GUI toolkit that starts the event
   loop.

In addition to starting the GUI event loops in one of these two ways, IPython
will *always* create an appropriate GUI application object when GUi
integration is enabled.

If you want your GUI apps to run in IPython you need to do two things:

1. Test to see if there is already an existing main application object. If
   there is, you should use it. If there is not an existing application object
   you should create one.
2. Test to see if the GUI event loop is running. If it is, you should not
   start it. If the event loop is not running you may start it.

This module contains functions for each toolkit that perform these things
in a consistent manner. Because of how PyOS_InputHook runs the event loop
you cannot detect if the event loop is running using the traditional calls
(such as ``wx.GetApp.IsMainLoopRunning()`` in wxPython). If PyOS_InputHook is
set These methods will return a false negative. That is, they will say the
event loop is not running, when is actually is. To work around this limitation
we proposed the following informal protocol:

* Whenever someone starts the event loop, they *must* set the ``_in_event_loop``
  attribute of the main application object to ``True``. This should be done
  regardless of how the event loop is actually run.
* Whenever someone stops the event loop, they *must* set the ``_in_event_loop``
  attribute of the main application object to ``False``.
* If you want to see if the event loop is running, you *must* use ``hasattr``
  to see if ``_in_event_loop`` attribute has been set. If it is set, you
  *must* use its value. If it has not been set, you can query the toolkit
  in the normal manner.
* If you want GUI support and no one else has created an application or
  started the event loop you *must* do this. We don't want projects to
  attempt to defer these things to someone else if they themselves need it.

The functions below implement this logic for each GUI toolkit. If you need
to create custom application subclasses, you will likely have to modify this
code for your own purposes. This code can be copied into your own project
so you don't have to depend on IPython.

.. _matplotlib_support:

Plotting with matplotlib
========================

.. magic:: matplotlib

`matplotlib` provides high quality 2D and 3D plotting for Python. `matplotlib`
can produce plots on screen using a variety of GUI toolkits, including Tk,
PyGTK, PyQt4 and wxPython. It also provides a number of commands useful for
scientific computing, all with a syntax compatible with that of the popular
Matlab program.

To start IPython with matplotlib support, use the ``--matplotlib`` switch. If
IPython is already running, you can run the :magic:`matplotlib` magic.  If no
arguments are given, IPython will automatically detect your choice of
matplotlib backend.  You can also request a specific backend with
``%matplotlib backend``, where ``backend`` must be one of: 'tk', 'qt', 'wx',
'gtk', 'osx'.  In the web notebook and Qt console, 'inline' is also a valid
backend value, which produces static figures inlined inside the application
window instead of matplotlib's interactive figures that live in separate
windows.


.. _interactive_demos:

Interactive demos with IPython
==============================

IPython ships with a basic system for running scripts interactively in
sections, useful when presenting code to audiences. A few tags embedded
in comments (so that the script remains valid Python code) divide a file
into separate blocks, and the demo can be run one block at a time, with
IPython printing (with syntax highlighting) the block before executing
it, and returning to the interactive prompt after each block. The
interactive namespace is updated after each block is run with the
contents of the demo's namespace.

This allows you to show a piece of code, run it and then execute
interactively commands based on the variables just created. Once you
want to continue, you simply execute the next block of the demo.

In order to run a file as a demo, you must first make a Demo object out
of it. If the file is named myscript.py, the following code will make a
demo:

.. sourcecode:: ipython

    from IPython.lib.demo import Demo
    mydemo = Demo('myscript.py')


This creates the 'mydemo' object, whose blocks you run one at a time by
simply calling the object with no arguments. Then call it to run each step
of the demo::

    mydemo()

Demo objects can be restarted, you can move forward or back skipping blocks,
re-execute the last block, etc.

See the :mod:`IPython.lib.demo` module and the
:class:`~IPython.lib.demo.Demo` class for details.

Limitations:
------------

These demos are limited to fairly simple uses. In particular, you cannot
break up sections within indented code.

I.E. (loops, if statements, function definitions, etc.)

Supporting something like this would basically require tracking the
internal execution state of the Python interpreter, so only top-level
divisions are allowed.


.. tip::

   If you want to be able to open an IPython
   instance at an arbitrary point in a program, you can use IPython's
   :ref:`embedding facilities <Embedding>`.

.. .. include:: links.txt
