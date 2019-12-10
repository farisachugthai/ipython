.. _config_intro:

============================================
Overview of the IPython configuration system
============================================

.. module:: intro
   :synopsis: Introduce IPython.

.. why was this previously in development???

Configuration file location
===========================

So where should you put your configuration files? IPython uses "profiles" for
configuration, and by default, all profiles will be stored in the so called
"IPython directory". The location of this directory is determined by the
following algorithm:

* If the ``ipython-dir`` command line flag is given, its value is used.

* If not, the value returned by :func:`IPython.paths.get_ipython_dir`
  is used. This function will first look at the :envvar:`IPYTHONDIR`
  environment variable and then default to :file:`~/.ipython`.
  Historical support for the :envvar:`IPYTHON_DIR` environment variable will
  be removed in a future release.

For most users, the configuration directory will be :file:`~/.ipython`.

Previous versions of IPython on Linux would use the XDG config directory,
creating :file:`~/.config/ipython` by default. We have decided to go
back to :file:`~/.ipython` for consistency among systems. IPython will
issue a warning if it finds the XDG location, and will move it to the new
location if there isn't already a directory there.

Once the location of the IPython directory has been determined, you need to know
which profile you are using. For users with a single configuration, this will
simply be 'default', and will be located in
:file:`<IPYTHONDIR>/profile_default`.

The next thing you need to know is what to call your configuration file. The
basic idea is that each application has its own default configuration filename.
The default named used by the :command:`ipython` command line program is
:file:`ipython_config.py`, and *all* IPython applications will use this file.
The IPython kernel will load its own config file *after*
:file:`ipython_config.py`. To load a particular configuration file instead of
the default, the name can be overridden by the ``config_file`` command line
flag.

To generate the default configuration files, do::

    $ ipython profile create

and you will have a default :file:`ipython_config.py` in your IPython directory
under :file:`profile_default`.

.. note::

    IPython configuration options are case sensitive, and IPython cannot
    catch misnamed keys or invalid values.

    By default IPython will also ignore any invalid configuration files.

.. versionadded:: 5.0

    IPython can be configured to abort in case of invalid configuration file.
    To do so set the environment variable ``IPYTHON_SUPPRESS_CONFIG_ERRORS`` to
    `'1'` or `'true'`


Locating these files
--------------------

From the command-line, you can quickly locate the :envvar:`IPYTHONDIR`
or a specific profile with:

.. sourcecode:: bash

    $ ipython locate
    /home/you/.ipython

    $ ipython locate profile foo
    /home/you/.ipython/profile_foo

These map to the utility functions: :func:`IPython.utils.path.get_ipython_dir`
and :func:`IPython.utils.path.locate_profile` respectively.
