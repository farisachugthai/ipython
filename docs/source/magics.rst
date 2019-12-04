.. _magic:

====================
Magic command system
====================

.. module:: magics-overview
   :synopsis: Review the magic system.

IPython will treat any line whose first character is a :kbd:`%` as a special
call to a 'magic' function.

These allow you to control the behavior of IPython itself, plus a lot of
system-type features. All magics are prefixed with a :kbd:`%` character, but
`~IPython.core.magic_parameters` are given without parentheses or quotes.

Lines that begin with :kbd:`%%` signal a `cell_magic`.

They take as arguments not only the rest of the current line, but all lines
in the current execution block are interpreted as arguments to the magic.

Cell magics can, in fact, make arbitrary modifications to the input they
receive, which need not even be valid Python code at all.

They receive the whole block as a single `str`.

As a line magic example, the :magic:`cd` magic works just like the OS command of
the same name::

      In [8]: %cd
      /home/fperez

The following uses the builtin :magic:`timeit` in cell mode::

   In [10]: %%timeit x = range(10000)
      ...: min(x)
      ...: max(x)
      ...:
   1000 loops, best of 3: 438 us per loop

In this case, ``x = range(10000)`` is called as the line argument, and the
block with ``min(x)`` and ``max(x)`` is called as the cell body.  The
:magic:`timeit` magic receives both.


Automagic
---------

.. magic:: automagic

If you have 'automagic' enabled (as it is by default), you don't need to type in
the single ``%`` explicitly for line magics; IPython will scan its internal
list of magic functions and call one if it exists. With automagic on you can
then just type `%cd` mydir to go to directory 'mydir'::

   In [9]: cd mydir
   /home/fperez/mydir

Cell magics *always* require an explicit ``%%`` prefix, automagic
calling only works for line magics.

The automagic system has the lowest possible precedence in name searches, so
you can freely use variables with the same names as magic commands. If a magic
command is 'shadowed' by a variable, you will need the explicit ``%`` prefix to
use it:

.. sourcecode:: ipython

    In [1]: cd ipython     # %cd is called by automagic
    /home/fperez/ipython

    In [2]: cd=1 	   # now cd is just a variable

    In [3]: cd .. 	   # and doesn't work as a function anymore
    File "<ipython-input-3-9fedb3aff56c>", line 1
      cd ..
          ^
    SyntaxError: invalid syntax


    In [4]: %cd .. 	   # but %cd always works
    /home/fperez

    In [5]: del cd     # if you remove the cd variable, automagic works again

    In [6]: cd ipython

    /home/fperez/ipython

Line magics, if they return a value, can be assigned to a variable using the
syntax ``l = %sx ls`` (which in this particular case returns the result of
:command:`ls` as a python `list`).

.. see:: :ref:`below <manual_capture>` for more information.

Type `%magic` for more information, including a list of all available magic
functions at any time and their docstrings. You can also type
``%magic_function_name?`` (see :ref:`below <dynamic_object_info>` for
information on the '?' system) to get information about any particular magic
function you are interested in.

The API documentation for the :mod:`IPython.core.magic` module contains the full
docstrings of all currently available magic commands.

.. seealso::

   :doc:`magics`
     A list of the line and cell magics available in IPython by default

   :ref:`defining_magics`
     How to define and register additional magic functions


.. _interactive-use:

Interactive use
===============

IPython is meant to work as a drop-in replacement for the standard interactive
interpreter. As such, any code which is valid python should execute normally
under IPython (cases where this is not true should be reported as bugs). It
does, however, offer many features which are not available at a standard python
prompt. What follows is a list of these.

Access to the standard Python help
----------------------------------

Simply type ``help()`` to access Python's standard help system. You can
also type ``help(object)`` for information about a given object, or
``help('keyword')`` for information on a keyword. You may need to configure your
:envvar:`PYTHONDOCS` environment variable for this feature to work correctly.


.. _dynamic_object_info:

Dynamic object information
--------------------------

Typing ``?word`` or ``word?`` prints detailed information about an object. If
certain strings in the object are too long (e.g. function signatures) they get
snipped in the center for brevity. This system gives access variable types and
values, docstrings, function prototypes and other useful information.

If the information will not fit in the terminal, it is displayed in a pager
(``less`` if available, otherwise a basic internal pager).

Typing ``??word`` or ``word??`` gives access to the full information, including
the source code where possible. Long strings are not snipped.

The following magic functions are particularly useful for gathering
information about your working environment:

    * :magic:`pdoc` **<object>**: Print (or run through a pager if too long) the
      docstring for an object. If the given object is a class, it will
      print both the class and the constructor docstrings.

    * :magic:`pdef` **<object>**: Print the call signature for any callable
      object. If the object is a class, print the constructor information.

    * :magic:`psource` **<object>**: Print (or run through a pager if too long)
      the source code for an object.

    * :magic:`pfile` **<object>**: Show the entire source file where an object was
      defined via a pager, opening it at the line where the object
      definition begins.

    * :magic:`who` / :magic:`whos`: These functions give information about identifiers
      you have defined interactively (not things you loaded or defined
      in your configuration files). %who just prints a list of
      identifiers and `%whos` prints a table with some basic details about
      each identifier.

The dynamic object information functions (:kbd:`?` / :kbd:`??` , `%pdoc`,
`%pfile`, `%pdef`, `%psource`) work on object attributes, as well as
directly on variables. For example, after doing ``import os``, you can use
``os.path.abspath??``.


Command line completion
-----------------------

At any time, hitting :kbd:`TAB` will complete any available python commands or
variable names, and show you a list of the possible completions if
there's no unambiguous one. It will also complete filenames in the
current directory if no python names match what you've typed so far.


Search command history
----------------------

IPython provides two ways for searching through previous input and thus
reduce the need for repetitive typing:

   1. Start typing, and then use the up and down arrow keys (or :kbd:`Ctrl-p`
      and :kbd:`Ctrl-n`) to search through only the history items that match
      what you've typed so far.
   2. Hit :kbd:`Ctrl-r`: to open a search prompt. Begin typing and the system
      searches your history for lines that contain what you've typed so
      far, completing as much as it can.

IPython will save your input history when it leaves and reload it next
time you restart it. By default, the history file is named
:file:`.ipython/profile_{name}/history.sqlite`.

Autoindent
----------

Starting with 5.0, IPython uses `prompt_toolkit` in place of :mod:`readline`,
it thus can recognize lines ending in ':' and indent the next line,
while also indenting automatically after `raise` or `return`,
and support real multi-line editing as well as syntactic coloration
during edition.

This feature does not use the ``readline`` library anymore, so it will
not honor your :file:`~/.inputrc` configuration (or whatever
file your :envvar:`INPUTRC` environment variable points to).

In particular if you want to change the input mode to ``vi``, you will need to
set the :trait:`TerminalInteractiveShell.editing_mode`
configuration  option of IPython.


Session logging and restoring
-----------------------------

.. option:: --logfile

You can log all input from a session either by starting IPython with the
command line switch ``--logfile=foo.py``.

(See :ref:`here <command_line_options>`)

In addition, this can be initialized at any moment with the magic function
:magic:`logstart`.

Log files can later be reloaded by running them as scripts and IPython
will attempt to `%replay` the log by executing all the lines in it, thus
restoring the state of a previous session. This feature is not quite
perfect, but can still be useful in many cases.

The log files can also be used as a way to have a permanent record of
any code you wrote while experimenting. Log files are regular text files
which you can later open in your favorite text editor to extract code or
to 'clean them up' before using them to replay a session.

The :magic:`logstart` function for activating logging in mid-session is used as
follows:

.. program:: %logstart [log_name [log_mode]]

.. option:: log_name

If no name is given, 'logname' defaults to a file named 'ipython_log.py' in your
current working directory, in 'rotate' mode (see below).

'`%logstart` name' saves to file *name* in 'backup' mode. It saves your
history up to that point and then continues logging.

.. option:: log_mode

`%logstart` takes a second optional parameter: logging mode. This can be
one of (note that the modes are given unquoted):

    * [over:] overwrite existing log_name.

    * [backup:] rename (if exists) to log_name~ and start log_name.

    * [append:] well, that says it.

    * [rotate:] create rotating logs log_name.1~, log_name.2~, etc.

.. option:: -o, --output

Adding the '-o' flag to '%logstart' magic (as in '%logstart -o [log_name [log_mode]]')
will also include output from iPython in the log file.

The :magic:`%logoff` and :magic:`%logon` functions allow you to
temporarily stop and resume logging to a file which had previously
been started with `%logstart`.

They will fail (with an explanation) if you try to use them
before logging has been started.

.. _system_shell_access:

System shell access
-------------------

Any input line beginning with a :kbd:`!` character is passed verbatim (minus
the :kbd:`!`) to the underlying operating system. For example,
typing ``!ls`` will run :command:`ls` in the current directory.


.. _manual_capture:

Manual capture of command output and magic output
-------------------------------------------------

You can assign the result of a system command to a Python variable with the
syntax ``myfiles = !ls``. Similarly, the result of a magic (as long as it returns
a value) can be assigned to a variable.  For example, the syntax ``myfiles = %sx ls``
is equivalent to the above system command example (the :magic:`sx` magic runs a shell command
and captures the output).  Each of these gets machine
readable output from stdout (e.g. without colours), and splits on newlines. To
explicitly get this sort of output without assigning to a variable, use two
exclamation marks (``!!ls``) or the :magic:`sx` magic command without an assignment.
(However, ``!!`` commands cannot be assigned to a variable.)

The captured list in this example has some convenience features. ``myfiles.n`` or ``myfiles.s``
returns a string delimited by newlines or spaces, respectively. ``myfiles.p``
produces `path objects <http://pypi.python.org/pypi/path.py>`_ from the list items.
See :ref:`string_lists` for details.

IPython also allows you to expand the value of python variables when
making system calls. Wrap variables or expressions in {braces}::

    In [1]: pyvar = 'Hello world'
    In [2]: !echo "A python variable: {pyvar}"
    A python variable: Hello world
    In [3]: import math
    In [4]: x = 8
    In [5]: !echo {math.factorial(x)}
    40320

For simple cases, you can alternatively prepend $ to a variable name::

    In [6]: !echo $sys.argv
    [/home/fperez/usr/bin/ipython]
    In [7]: !echo "A system variable: $$HOME"  # Use $$ for literal $
    A system variable: /home/fperez

Note that `$$` is used to represent a literal `$`.

System command aliases
----------------------

The :magic:`alias` magic function allows you to define magic functions which are in fact
system shell commands. These aliases can have parameters.

``%alias alias_name cmd`` defines 'alias_name' as an alias for 'cmd'

Then, typing ``alias_name params`` will execute the system command 'cmd
params' (from your underlying operating system).

You can also define aliases with parameters using ``%s`` specifiers (one per
parameter). The following example defines the parts function as an
alias to the command ``echo first %s second %s`` where each ``%s`` will be
replaced by a positional parameter to the call to %parts::

    In [1]: %alias parts echo first %s second %s
    In [2]: parts A B
    first A second B
    In [3]: parts A
    ERROR: Alias <parts> requires 2 arguments, 1 given.

If called with no parameters, :magic:`alias` prints the table of currently
defined aliases.

The :magic:`rehashx` magic allows you to load your entire $PATH as
ipython aliases. See its docstring for further details.


.. _dreload:

Recursive reload
----------------

The :mod:`IPython.lib.deepreload` module allows you to recursively reload a
module: changes made to any of its dependencies will be reloaded without
having to exit. To start using it, do::

    from IPython.lib.deepreload import reload as dreload


Verbose and colored exception traceback printouts
-------------------------------------------------

IPython provides the option to see very detailed exception tracebacks,
which can be especially useful when debugging large programs. You can
run any Python file with the %run function to benefit from these
detailed tracebacks. Furthermore, both normal and verbose tracebacks can
be colored (if your terminal supports it) which makes them much easier
to parse visually.

See the magic :magic:`xmode` and :magic:`colors` functions for details.

These features are basically a terminal version of Ka-Ping Yee's cgitb
module, now part of the standard Python library.


.. _input_caching:

Input caching system
--------------------

IPython offers numbered prompts (In/Out) with input and output caching
(also referred to as 'input history'). All input is saved and can be
retrieved as variables (besides the usual arrow key recall), in
addition to the :magic:`rep` magic command that brings a history entry
up for editing on the next command line.

The following variables always exist:

* ``_i``, ``_ii``, ``_iii``: store previous, next previous and next-next
  previous inputs.

* ``In``, ``_ih`` : a list of all inputs; ``_ih[n]`` is the input from line
  ``n``. If you overwrite In with a variable of your own, you can remake the
  assignment to the internal list with a simple ``In=_ih``.

Additionally, global variables named ``_i<n>`` are dynamically created (``<n>``
being the prompt counter), so ``_i<n> == _ih[<n>] == In[<n>]``.

For example, what you typed at prompt 14 is available as ``_i14``, ``_ih[14]``
and ``In[14]``.

This allows you to easily cut and paste multi line interactive prompts
by printing them out: they print like a clean string, without prompt
characters. You can also manipulate them like regular variables (they
are strings), modify or exec them.

You can also re-execute multiple lines of input easily by using the magic
:magic:`rerun` or :magic:`macro` functions. The macro system also allows you to
re-execute previous lines which include magic function calls (which require
special processing). Type %macro? for more details on the macro system.

A history function :magic:`history` allows you to see any part of your input
history by printing a range of the _i variables.

You can also search ('grep') through your history by typing
``%hist -g somestring``. This is handy for searching for URLs, IP addresses,
etc. You can bring history entries listed by '%hist -g' up for editing
with the %recall command, or run them immediately with :magic:`rerun`.

.. _output_caching:

Output caching system
---------------------

For output that is returned from actions, a system similar to the input
cache exists but using _ instead of _i. Only actions that produce a
result (NOT assignments, for example) are cached. If you are familiar
with Mathematica, IPython's _ variables behave exactly like
Mathematica's :kbd:`%` variables.

The following variables always exist:

    * [_] (a single underscore): stores previous output, like Python's
      default interpreter.
    * [__] (two underscores): next previous.
    * [___] (three underscores): next-next previous.

Additionally, global variables named _<n> are dynamically created (<n>
being the prompt counter), such that the result of output <n> is always
available as _<n> (don't use the angle brackets, just the number, e.g.
``_21``).

These variables are also stored in a global dictionary (not a
list, since it only has entries for lines which returned a result)
available under the names _oh and Out (similar to _ih and In). So the
output from line 12 can be obtained as ``_12``, ``Out[12]`` or ``_oh[12]``. If you
accidentally overwrite the Out variable you can recover it by typing
``Out=_oh`` at the prompt.

This system obviously can potentially put heavy memory demands on your
system, since it prevents Python's garbage collector from removing any
previously computed results. You can control how many results are kept
in memory with the configuration option ``InteractiveShell.cache_size``.
If you set it to 0, output caching is disabled. You can also use the :magic:`reset`
and :magic:`xdel` magics to clear large items from memory.

Directory history
-----------------

Your history of visited directories is kept in the global list _dh, and
the magic :magic:`cd` command can be used to go to any entry in that list. The
:magic:`dhist` command allows you to view this history. Do ``cd -<TAB>`` to
conveniently view the directory history.


Automatic parentheses and quotes
--------------------------------

These features were adapted from Nathan Gray's LazyPython. They are
meant to allow less typing for common situations.

Callable objects (i.e. functions, methods, etc) can be invoked like this
(notice the commas between the arguments)::

    In [1]: callable_ob arg1, arg2, arg3
    ------> callable_ob(arg1, arg2, arg3)

.. note::
   This feature is disabled by default. To enable it, use the ``%autocall``
   magic command. The commands below with special prefixes will always work,
   however.

You can force automatic parentheses by using '/' as the first character
of a line. For example::

    In [2]: /globals # becomes 'globals()'

Note that the '/' MUST be the first character on the line! This won't work::

    In [3]: print /globals # syntax error

In most cases the automatic algorithm should work, so you should rarely
need to explicitly invoke /. One notable exception is if you are trying
to call a function with a list of tuples as arguments (the parenthesis
will confuse IPython)::

    In [4]: zip (1,2,3),(4,5,6) # won't work

but this will work::

    In [5]: /zip (1,2,3),(4,5,6)
    ------> zip ((1,2,3),(4,5,6))
    Out[5]: [(1, 4), (2, 5), (3, 6)]

IPython tells you that it has altered your command line by displaying
the new command line preceded by ``--->``.

You can force automatic quoting of a function's arguments by using ``,``
or ``;`` as the first character of a line. For example::

    In [1]: ,my_function /home/me  # becomes my_function("/home/me")

If you use ';' the whole argument is quoted as a single string, while ',' splits
on whitespace::

    In [2]: ,my_function a b c    # becomes my_function("a","b","c")

    In [3]: ;my_function a b c    # becomes my_function("a b c")

Note that the ',' or ';' MUST be the first character on the line! This
won't work::

    In [4]: x = ,my_function /home/me # syntax error

