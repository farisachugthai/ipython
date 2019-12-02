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


Features
========

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
  (simpler than changing :envvar:`$PYTHONSTARTUP` environment variables
  every time).

* Session logging and reloading.

* Extensible syntax processing for special purpose situations.

* Access to the system shell with user-extensible alias system.

* Easily embeddable in other Python programs and GUIs.

* Integrated access to the pdb debugger and the Python profiler.


Command Line Interface
======================

The Command line interface inherits the above functionality and adds

* real multi-line editing thanks to `prompt_toolkit
  <http://python-prompt-toolkit.readthedocs.io/en/stable/>`_.

* syntax highlighting as you type

* integration with command line editor for a better workflow.

The kernel also has its share of features. When used with a compatible frontend,
it allows:

* the object to create a rich display of Html, Images, Latex, Sound and
  Video.

* interactive widgets with the use of the `ipywidgets
  <http://ipywidgets.readthedocs.io/en/stable/>`_ package.


This documentation will walk you through the features of the IPython shell
and kernel, as well as describe their internal mechanisms in order
to improve your Python workflow.

You can find the Table of Contents for this documentation in the left
sidebar, allowing you to come back to previous sections or skip ahead, if needed.

The latest development version is always available from IPython's `GitHub
repository <http://github.com/ipython/ipython>`_.


Index
=====

.. toctree::
   :maxdepth: 2
   :caption: Introduction

   overview
   install/index

.. toctree::
   :maxdepth: 3
   :caption: Tutorial

   tutorial/index
   config
   magics
   custommagics
   details


.. toctree::
   :maxdepth: 2
   :caption: Extending

   integrating
   shell_mimerenderer
   eventloops
   inputtransforms
   callbacks
   extensions
   sphinxext/index


.. toctree::
   :maxdepth: 1
   :titlesonly:
   :caption: Developer's Notes

   options/index
   development/index
   building
   coredev
   reference
   todo


.. toctree::
   :maxdepth: 4
   :caption: API

   api/index


.. toctree::
   :maxdepth: 1
   :titlesonly:
   :caption: About us

   whatsnew/index
   history
   license_and_copyright


.. only:: html

   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`
