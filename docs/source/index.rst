.. _introduction:

=====================
IPython Documentation
=====================

.. only:: html

   :Release: |release|
   :Date: |today|

Welcome to the official IPython documentation

IPython provides a rich toolkit to help you make the most of using Python
interactively.  Its main components are:

* A powerful interactive Python shell


.. image:: /_images/ipython-6-screenshot.png
    :alt: Screenshot of IPython 6.0
    :align: center


* A `Jupyter <https://jupyter.org/>`_ kernel to work with Python code in Jupyter
  notebooks and other interactive frontends.

The enhanced interactive Python shells and kernel have the following main
features:

* Comprehensive object introspection.

* Input history, persistent across sessions.

* Caching of output results during a session with automatically generated
  references.

* Extensible tab completion, with support by default for completion of python
  variables and keywords, filenames and function keywords.

* Extensible system of 'magic' commands for controlling the environment and
  performing many tasks related to IPython or the operating system.

* A rich configuration system with easy switching between different setups
  (simpler than changing ``$PYTHONSTARTUP`` environment variables every time).

* Session logging and reloading.

* Extensible syntax processing for special purpose situations.

* Access to the system shell with user-extensible alias system.

* Easily embeddable in other Python programs and GUIs.

* Integrated access to the pdb debugger and the Python profiler.


The Command line interface inherits the above functionality and adds

* real multi-line editing thanks to `prompt_toolkit <http://python-prompt-toolkit.readthedocs.io/en/stable/>`_.

* syntax highlighting as you type

* integration with command line editor for a better workflow.

The kernel also has its share of features. When used with a compatible frontend,
it allows:

* the object to create a rich display of Html, Images, Latex, Sound and
  Video.

* interactive widgets with the use of the `ipywidgets <http://ipywidgets.readthedocs.io/en/stable/>`_ package.


This documentation will walk you through most of the features of the IPython
command line and kernel, as well as describe the internal mechanisms in order
to improve your Python workflow.

You can find the table of content for this documentation in the left
sidebar, allowing you to come back to previous sections or skip ahead, if needed.


The latest development version is always available from IPython's `GitHub
repository <http://github.com/ipython/ipython>`_.





IPython Documentation
---------------------

This directory contains the majority of the documentation for IPython.


Deploy docs
-----------

Documentation is automatically deployed on ReadTheDocs on every push or merged
Pull requests.


Requirements
------------

The documentation must be built using Python 3.

In additions to :ref:`devinstall`,
the following tools are needed to build the documentation:

 - sphinx
 - sphinx_rtd_theme
 - docrepr

In a conda environment, or a Python 3 ``venv``, you should be able to run::

  cd ipython
  pip install -U -r docs/requirements.txt


Build Commands
--------------

The documentation gets built using ``make``, and comes in several flavors.

``make html`` - build the API and narrative documentation web pages, this is
the default ``make`` target, so running just ``make`` is equivalent to ``make
html``.

``make html_noapi`` - same as above, but without running the auto-generated API
docs. When you are working on the narrative documentation, the most time
consuming portion  of the build process is the processing and rending of the
API documentation. This build target skips that.

``make pdf`` will compile a pdf from the documentation.

You can run ``make help`` to see information on all possible make targets.

To save time,
the make targets above only process the files that have been changed since the
previous docs build.
To remove the previous docs build you can use ``make clean``.
You can also combine ``clean`` with other `make` commands;
for example,
``make clean html`` will do a complete rebuild of the docs or `make clean pdf` will do a complete build of the pdf.


Continuous Integration
----------------------

Documentation builds are included in the Travis-CI continuous integration process,
so you can see the results of the docs build for any pull request at
https://travis-ci.org/ipython/ipython/pull_requests.


See Also
--------
.. seealso::

   `Jupyter documentation <http://jupyter.readthedocs.io/en/latest/>`_
     The Jupyter documentation provides information about the Notebook code and other Jupyter sub-projects.

   `ipyparallel documentation <http://ipyparallel.readthedocs.io/en/latest/>`_
     Formerly ``IPython.parallel``.


.. toctree::
   :maxdepth: 1
   :caption: Table of Contents

   overview
   install/index
   interactive/index
   config/index
   magics
   extending/index
   extensions/index
   sphinxext/index
   development/index
   coredev
   api/index
   reference
   todo
   whatsnew/index
   about/index


.. only:: html

   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`
