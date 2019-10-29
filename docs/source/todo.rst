.. _todo:

====
TODO
====

:orphan:

:date: Oct 27, 2019

These are just my personal observations of things that need to get fixed up.

Remove all references to `IPython.core.inputtransformer` and `IPython.core.inputsplitter` in the tests.

It was successfully removed from the code base but hasn't been from
the tests.

Flatten the docs they're really hard to navigate.

The get_ipython().db attribute is seemingly completely undocumented.

I just happened to stumble upon it while rummaging through the tests but why.

Continue working on the sphinxext docs and also consider rewriting our directive.

Docs still don't build.

YES THEY DO! Got them working again and now it's a lot cleaner and emits way less warnings.

Nosetests works.
Pytest will collect ~500 modules and crash.


Command line options
--------------------

Oct 29, 2019:

Did I do something wrong or does the quick option still execute startup files?

.. sourcecode:: bash

   * $: ipython --quick

   Python 3.7.3 (default, Apr  3 2019, 19:16:38)
   Type 'copyright', 'credits' or 'license' for more information

   IPython 7.10.0.dev -- An enhanced Interactive Python. Type '?' for help.
   [TerminalIPythonApp] WARNING | Unknown error in handling startup files:
