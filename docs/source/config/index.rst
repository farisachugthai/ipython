.. _config_index:

===============================
Configuration and customization
===============================

.. module:: configuration
   :synopsis: Configure the shell and introduce profiles.

.. highlight:: ipython


.. _setting_config:

Setting configurable options
============================

Many of IPython's classes have configurable attributes (see
:doc:`../api/index` for the list). These can be
configured in several ways.

Python config files
-------------------

To create the blank config files, run::

    ipython profile create [profilename]

If you leave out the profile name, the files will be created for the
``default`` profile (see :ref:`profiles`). These will typically be
located in :file:`~/.ipython/profile_default/`, and will be named
:file:`ipython_config.py`, :file:`ipython_notebook_config.py`, etc.
The settings in :file:`ipython_config.py` apply to all IPython commands.

The files typically start by getting the root config object::

    c = get_config()

You can then configure class attributes like this::

    c.InteractiveShell.automagic = False

Be careful with spelling--incorrect names will simply be ignored, with
no error.

To add to a collection which may have already been defined elsewhere,
you can use methods like those found on:

* lists

* dicts and sets

   - append
   - extend
   - :meth:`~traitlets.config.LazyConfigValue.prepend` (like extend, but at the front)
   - add
   - update (which works both for dicts and sets)

.. todo:: So I just formatted that but we should also check if that's still true.

::

    c.InteractiveShellApp.extensions.append('Cython')

.. versionadded:: 2.0
   list, dict and set methods for config values

Example config file
-------------------

::

    # sample ipython_config.py
    c = get_config()

    c.TerminalIPythonApp.display_banner = True
    c.InteractiveShellApp.log_level = 20
    c.InteractiveShellApp.extensions = [
        'myextension'
    ]
    c.InteractiveShellApp.exec_lines = [
        'import numpy',
        'import scipy'
    ]
    c.InteractiveShellApp.exec_files = [
        'mycode.py',
        'fancy.ipy'
    ]
    c.InteractiveShell.colors = 'LightBG'
    c.InteractiveShell.confirm_exit = False
    c.InteractiveShell.editor = 'nano'
    c.InteractiveShell.xmode = 'Context'

    c.PrefilterManager.multi_line_specials = True

    c.AliasManager.user_aliases = [
     ('la', 'ls -al')
    ]


Command line arguments
----------------------

Every configurable value can be set from the command line, using this
syntax::

    ipython --ClassName.attribute=value

Many frequently used options have short aliases and flags. For example:

.. option:: --matplotlib

   To integrate with a matplotlib GUI event loop.

.. option:: --pdb

   Automatic post-mortem debugging of exceptions.

To see all of these abbreviated options, run::

    ipython --help
    ipython notebook --help
    # etc.

Options specified at the command line, in either format, override
options set in a configuration file.

The config magic
----------------

You can also modify config from inside IPython, using a magic command::

    %config IPCompleter.greedy = True

Running `%config` with no arguments will list all of the different
`traitlets.traitlets.Configurable` classes bound to the shell.

This will allow you to see what choices you have, and rerun the `%config`
command with your desired arguments.

In addition, the :kbd:`Tab` key can be used for autocompletion, and the shell
will automatically know how to only display valid configuration options.

For example::

   >>> In [36]: %config TerminalInteractiveShell
   >>> In [37]: %config TerminalInteractiveShell.ast_node_interactivity = 'last_expr_or_assign'

At present, this only affects the current session - changes you make to
config are not saved anywhere. Also, some options are only read when
IPython starts, so they can't be changed like this.


.. _configure_start_ipython:

Running IPython from Python
----------------------------

If you are using :ref:`embedding` to start IPython from a normal
python file, you can set configuration options the same way as in a
config file by creating a traitlets config object and passing it to
:func:`~IPython.start_ipython` like in the example below.

.. error:: Where is the example?


.. _profiles:

Profiles
========

.. option:: --profile

   IPython can use multiple profiles, with separate configuration and
   history. By default, if you don't specify a profile, IPython always runs
   in the ``default`` profile.

To use a new profile::

    ipython profile create foo   # create the profile foo
    ipython --profile=foo        # start IPython using the new profile

Profiles are typically stored in :ref:`ipythondir`, but you can also keep
a profile in the current working directory, for example to distribute it
with a project.

To find a profile directory on the filesystem::

    ipython locate profile foo


.. _ipythondir:

The IPython directory
=====================

IPython stores its files --- config, command history and extensions --- in
the directory :file:`~/.ipython/` by default.

.. envvar:: IPYTHONDIR

   If set, this environment variable should be the path to a directory,
   which IPython will use for user data. IPython will create it if it
   does not exist.

.. option:: --ipython-dir=<path>

   This command line option can also be used to override the default
   IPython directory.

.. toctree::

   intro
   details


.. seealso::

   :doc:`../development/index`
      Technical details of the config system.

Extending and integrating with IPython
--------------------------------------

.. toctree::
   :maxdepth: 2

   integrating
   custommagics
   shell_mimerenderer
   callbacks
   eventloops
