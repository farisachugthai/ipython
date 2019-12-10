.. _extensions_autoreload:

============
Auto-reload
============

.. magic:: autoreload

IPython extension to reload modules before executing user code.

``autoreload`` reloads modules automatically before entering the execution of
code typed at the IPython prompt.

This makes for example the following workflow possible:

.. sourcecode:: ipython

   In [1]: %load_ext autoreload

   In [2]: %autoreload 2

   In [3]: from foo import some_function

   In [4]: some_function()
   Out[4]: 42

   In [5]: # open foo.py in an editor and change some_function to return 43

   In [6]: some_function()
   Out[6]: 43

The module was reloaded without reloading it explicitly, and the object
imported with ``from foo import ...`` was also updated.

Examples
---------

The following magic commands are provided:

``%autoreload``

    Reload all modules (except those excluded by ``%aimport``)
    automatically now.

``%autoreload 0``

    Disable automatic reloading.

``%autoreload 1``

    Reload all modules imported with ``%aimport`` every time before
    executing the Python code typed.

``%autoreload 2``

    Reload all modules (except those excluded by ``%aimport``) every
    time before executing the Python code typed.

``%aimport``

    List modules which are to be automatically imported or not to be imported.

``%aimport foo``

    Import module 'foo' and mark it to be autoreloaded for ``%autoreload 1``

``%aimport foo, bar``

    Import modules 'foo', 'bar' and mark them to be autoreloaded for ``%autoreload 1``

``%aimport -foo``

    Mark module 'foo' to not be autoreloaded.

Caveats
-------

Reloading Python modules in a reliable way is in general difficult,
and unexpected things may occur. ``%autoreload`` tries to work around
common pitfalls by replacing function code objects and parts of
classes previously in the module with new versions. This makes the
following things to work:

- Functions and classes imported via 'from xxx import foo' are upgraded
  to new versions when 'xxx' is reloaded.

- Methods and properties of classes are upgraded on reload, so that
  calling 'c.foo()' on an object 'c' created before the reload causes
  the new code for 'foo' to be executed.

Some of the known remaining caveats are:

- Replacing code objects does not always succeed: changing a @property
  in a class to an ordinary method or a method to a member variable
  can cause problems (but in old objects only).

- Functions that are removed (eg. via monkey-patching) from a module
  before it is reloaded are not upgraded.

- C extension modules cannot be reloaded, and so cannot be autoreloaded.

.. _autoreload-api:

API Info
========

.. automodule:: IPython.extensions.autoreload
