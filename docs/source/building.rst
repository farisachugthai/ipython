.. _building:

================
Building IPython
================

.. module:: building-ipython
   :synopsis: Notes for those interested in contributing to IPython.


Documentation
=============

.. stole this from jupyter. thanks guys!

To build the documentation you'll need `Sphinx <http://www.sphinx-doc.org/>`_,
`pandoc <http://pandoc.org/>`_ and a few other packages.

To install (and activate) a `conda environment`_ named ``notebook_docs``
containing all the necessary packages (except pandoc), use::

    conda env create -f docs/environment.yml
    conda activate notebook_docs  # Linux and OS X
    activate notebook_docs         # Windows

.. _conda environment:
    https://conda.io/docs/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file

If you want to install the necessary packages with ``pip``, use the following instead::

    pip install -r docs/doc-requirements.txt

Once you have installed the required packages, you can build the docs with::

    cd docs
    make html

After that, the generated HTML files will be available at
``build/html/index.html``. You may view the docs in your browser.

You can automatically check if all hyperlinks are still valid::

    make linkcheck

Windows users can find ``make.bat`` in the ``docs`` folder.
I suppose this should go in the core dev dir but for the time being I'm going
to try and keep everything at the top level.

.. In case you're wondering, this section below was in a file at ipythondir/docs/README.
   But I was like 'Why not include it?'


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
 - ``sphinx_rtd_theme``
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

To save time, the make targets above only process the files that have
been changed since the previous docs build.

To remove the previous docs build you can use ``make clean``.

You can also combine ``clean`` with other `make` commands; for example,
``make clean html`` will do a complete rebuild of the docs or
``make clean pdf`` will do a complete build of the pdf.


Sphinx Integration
~~~~~~~~~~~~~~~~~~~~

Alternatively, running::

   sphinx-apidoc -f -e --tocfile index -o source/api/generated/ ../IPython "../IPython/*tests*"

Will generate the needed API documentation and running::

   sphinx-build -b html -c source -d build/.doctrees -P -w sphinx.log source build/html

Seems to cover most of what those make commands and our ``autogen_*`` scripts
do.


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


Testing
========

The IPython project currently uses ``nose`` for it's unit testing.

A :file:`../../IPython/conftest.py` file exists for usage with pytest;
however, this integration is still being actively worked on.

Quickstart
-----------
Install dependencies::

    pip install -e '.[test]'

To run the Python tests, use::

    pytest

If you want coverage statistics as well, you can run::

    py.test --cov notebook -v --pyargs notebook


Other
------
I don't know where to note this because it looks like these docs are devoid
of any mention of the test suite.

I simply wanted to note that we have a nose plugin; even though, it's not
well advertised.

.. code-block:: rst

   Adds a sphinx directive that can be used to automatically document a plugin.

   this::

    .. autoplugin :: nose.plugins.foo
       :plugin: Pluggy

   produces::

     .. automodule :: nose.plugins.foo

     Options
     -------

     .. cmdoption :: --foo=BAR, --fooble=BAR

       Do the foo thing to the new thing.

     Plugin
     ------

     .. autoclass :: nose.plugins.foo.Pluggy
        :members:


Tips
----

On usage in Vim:

.. code-block:: vim

   py3 from nose.core import run; run(vim.current.buffer, argv=[''])

Should work on both vim and neovim so long as python3 is setup correctly,
nose is installed in the current env, and the legacy python interface is
functional.

'argv' among many other keyword-parameters can be customized as desired.
