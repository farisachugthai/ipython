=================
How IPython works
=================

.. module:: how_ipython_works
   :synopsis: Review how IPython works 'under the hood'.

.. |ip| replace:: :class:`~IPython.core.interactiveshell.InteractiveShell`

.. moved kernel stuff out to wrapper kernels. This is gonna start housing
   profile info.


Terminal IPython
================

.. this is the developers section they know what a repl is.

Background
----------

When you type ``ipython``, you get the original IPython interface, running in
the terminal. It does something like this::

    while True:
        code = input(">>> ")
        exec(code)

Of course, it's much more complex, because it has to deal with multi-line
code, tab completion using :mod:`readline`, magic commands, and so on. But the
model is like that: prompt the user for some code, and when they've entered it,
exec it in the same process. This model is often called a REPL, or
Read-Eval-Print-Loop.


.. _profiles_dev:

How Profiles Are Setup
-----------------------

The profile directory is used by all IPython applications, to manage
configuration, logging and security.

Indeed the profile directory is the basis for all IPython configuration,
and as a result, depends on pre-existing state from other objects and mixins
the least.

A profile is a directory containing configuration and runtime files, such as
logs, connection info for the parallel apps, and your IPython command history.

The idea is that users often want to maintain a set of configuration files for
different purposes: one for doing numerical computing with NumPy and SciPy and
another for doing symbolic computing with SymPy. Profiles make it easy to keep a
separate configuration files, logs, and histories for each of these purposes.

Let's start by showing how a profile is used:

.. code-block:: bash

    $ ipython --profile=sympy

This tells the :command:`ipython` command line program to get its configuration
from the "sympy" profile. The file names for various profiles do not change. The
only difference is that profiles are named in a special way. In the case above,
the "sympy" profile means looking for :file:`ipython_config.py` in :file:`<IPYTHONDIR>/profile_sympy`.

The general pattern is this: simply create a new profile with:

.. code-block:: bash

    $ ipython profile create <name>

which adds a directory called ``profile_<name>`` to your IPython directory. Then
you can load this profile by adding ``--profile=<name>`` to your command line
options. Profiles are supported by all IPython applications.

IPython ships with some sample profiles in :file:`IPython/config/profile`. If
you create profiles with the name of one of our shipped profiles, these config
files will be copied over instead of starting with the automatically generated
config files.

IPython extends the config loader for Python files so that you can inherit
config from another profile. To do this, use a line like this in your Python
config file:

.. sourcecode:: python

    load_subconfig('ipython_config.py', profile='default')


Profile Initialization
----------------------

As a result, the ``ipython_dir`` and ``profile_dir`` attributes of the
|ip| object that drives the application are initialized first
with :meth:`init_profile_dir`.


:class:`IPython.core.profiledir.ProfileDir`
-------------------------------------------

This object knows how to find, create and manage these directories. This
should be used by any code that wants to handle profiles.


See Also
---------

Relevant Modules:

:mod:`IPython.paths`
:mod:`IPython.utils.path`
:mod:`IPython.core.profileapp`
:mod:`IPython.core.profiledir`
:mod:`IPython.core.interactiveshell`

Relevant Classes:

:class:`IPython.core.interactiveshell.InteractiveShell`
:class:`IPython.core.profileapp.ProfileApp`

.. yeah it's kinda spread all over

Relevant Docs:

:doc:`config`
:doc:`intro`

