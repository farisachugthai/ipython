.. _install_index:

============
Installation
============

.. module:: installation
   :synopsis: Root of installation instructions

.. highlight:: ipython

This section will guide you through :ref:`installing IPython itself <install>`,
and installing :ref:`kernels for Jupyter <kernel_install>` if you wish to
work with multiple version of Python, or you're working in
multiple environments.

IPython 6 requires Python ≥ 3.6. IPython 5.x can be installed on Python 2.


Quick Install
-------------

With ``pip`` already installed :

.. code-block:: bash

    $ pip install ipython

This installs IPython as well as its dependencies.

If you want to use IPython with notebooks or the Qt console, you should also
install Jupyter ``pip install jupyter``.

.. _installation-overview:

Overview
--------

This document describes in detail the steps required to install IPython. For a
few quick ways to get started with package managers or full Python
distributions, see `the install page <https://ipython.org/install.html>`_ of the
IPython website.

Please let us know if you have problems installing IPython or any of its
dependencies.

IPython and most dependencies should be installed via :command:`pip`.
In many scenarios, this is the simplest method of installing Python packages.
More information about :mod:`pip` can be found on
`its PyPI page <https://pip.pypa.io>`__.


More general information about installing Python packages can be found in
`Python's documentation <http://docs.python.org>`_.

.. _dependencies:

Dependencies
~~~~~~~~~~~~

IPython relies on a number of other Python packages. Installing using a package
manager like pip or conda will ensure the necessary packages are installed.
Manual installation without dependencies is possible, but not recommended.
The dependencies can be viewed with package manager commands,
such as :command:`pip show ipython` or :command:`conda info ipython`.


Installing IPython itself
~~~~~~~~~~~~~~~~~~~~~~~~~

IPython requires several dependencies to work correctly, it is not recommended
to install IPython and all its dependencies manually as this can be quite long
and troublesome. You should use the python package manager ``pip``.

Installation using pip
~~~~~~~~~~~~~~~~~~~~~~

Make sure you have the latest version of :mod:`pip` (the Python package
manager) installed. If you do not, head to `Pip documentation
<https://pip.pypa.io/en/stable/installing/>`_ and install :mod:`pip` first.

The quickest way to get up and running with IPython is to install it with pip:

.. code-block:: bash

    $ pip install ipython

That's it.


Installation from source
~~~~~~~~~~~~~~~~~~~~~~~~

To install IPython from source,
grab the latest stable tarball of IPython `from PyPI
<https://pypi.python.org/pypi/ipython>`__.  Then do the following:

.. code-block:: bash

    tar -xzf ipython-5.1.0.tar.gz
    cd ipython-5.1.0
    # The [test] extra ensures test dependencies are installed too:
    pip install .[test]

Do not invoke ``setup.py`` directly as this can have undesirable consequences
for further upgrades. We do not recommend using ``easy_install`` either.

If you are installing to a location (like ``/usr/local``) that requires higher
permissions, you may need to run the last command with :command:`sudo`. You can
also install in user specific location by using the ``--user`` flag in
conjunction with pip.

To run IPython's test suite, use the :command:`iptest` command from outside of
the IPython source tree:

.. code-block:: bash

    $ iptest

.. _devinstall:

Installing the development version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is also possible to install the development version of IPython from our
`Git <http://git-scm.com/>`_ source code repository.  To do this you will
need to have Git installed on your system.


Then do:

.. code-block:: bash

    $ git clone https://github.com/ipython/ipython.git
    $ cd ipython
    $ pip install -e .[test]

The :command:`pip` ``install -e .`` command allows users and developers to follow
the development branch as it changes by creating links in the right places and
installing the command line scripts to the appropriate locations.

Then, if you want to update your IPython at any time, do:

.. code-block:: bash

    $ git pull

If the dependencies or entrypoints have changed, you may have to run

.. code-block:: bash

    $ pip install -e .

again, but this is infrequent.

.. _installation-troubleshooting:

Troubleshooting
===============

.. admonition::

   This troubleshooting guide is old.

If you are encountering an error message you are likely trying to install or
use IPython from source. You need to checkout the remote 5.x branch. If you are
using git the following should work

.. code-block:: bash

  $ git fetch origin
  $ git checkout 5.x

If you encounter this error message with a regular install of IPython, then you
likely need to update your package manager, for example if you are using `pip`
check the version of pip with::

  $ pip --version

You will need to update pip to the version 9.0.1 or greater. If you are not using
pip, please inquiry with the maintainers of the package for your package
manager.

For more information see one of our blog posts:

    https://blog.jupyter.org/release-of-ipython-5-0-8ce60b8d2e8e

As well as the following Pull-Request for discussion:

    https://github.com/ipython/ipython/pull/9900

This error does also occur if you are invoking ``setup.py`` directly – which you
should not – or are using ``easy_install`` If this is the case, use ``pip
install .`` instead of ``setup.py install`` , and ``pip install -e .`` instead
of ``setup.py develop`` If you are depending on IPython as a dependency you may
also want to have a conditional dependency on IPython depending on the Python
version::

    install_req = ['ipython']
    if sys.version_info[0] < 3 and 'bdist_wheel' not in sys.argv:
        install_req.remove('ipython')
        install_req.append('ipython<6')

    setup(
        ...
        install_requires=install_req
    )


Aside on setuptools
--------------------

As a quick explanation for the instructions on how to invoke setup.py,
one can refer to the output of ``pip uninstall``.::

   python.exe -m pip uninstall [options] -r <requirements file> ...

   Description:
      Uninstall packages.

      pip is able to uninstall most installed packages. Known exceptions are:

   .. nested::

      - **Pure distutils packages installed with ``python setup.py install``, which
        leave behind no metadata to determine what files were installed.
      - Script wrappers installed by ``python setup.py develop``.**


.. todo:: So it says this docs is about kernel installs.

    It mostly seems like a wildly incomplete and out of date explanation of virtual environments?

.. seealso::

   :ref:`Installing Jupyter <jupyter:install>`
     The IPython kernel is the Python execution backend for Jupyter.

The Jupyter Notebook and other frontends automatically ensure that the
IPython kernel is available. However, if you want to use a kernel with a
different version of Python, or in a virtualenv or conda environment, you'll
need to install that manually.


Kernels for Python 2 and 3
--------------------------

If you're running Jupyter on Python 3, you can set up a Python 2 kernel after
checking your version of pip is greater than 9.0::

    python2 -m pip --version

Then install with ::

    python2 -m pip install ipykernel
    python2 -m ipykernel install --user

Or using conda, create a Python 2 environment::

    conda create -n ipykernel_py2 python=2 ipykernel
    conda activate ipykernel_py2
    python -m ipykernel install --user

.. note::

    IPython 6.0 stopped support for Python 2, so
    installing IPython on Python 2 will give you an older version (5.x series).

If you're running Jupyter on Python 2 and want to set up a Python 3 kernel,
follow the same steps, replacing ``2`` with ``3``.

The last command installs a :ref:`kernel spec <jupyterclient:kernelspecs>` file
for the current python installation. Kernel spec files are JSON files, which
can be viewed and changed with a normal text editor.

.. _multiple_kernel_install:

Kernels for different environments
----------------------------------

If you want to have multiple IPython kernels for different virtualenvs or conda
environments, you will need to specify unique names for the kernelspecs.

Make sure you have ipykernel installed in your environment. If you are using
``pip`` to install ``ipykernel`` in a conda env, make sure ``pip`` is
installed:

.. sourcecode:: bash

    source activate myenv
    conda install pip
    conda install ipykernel # or pip install ipykernel

For example, using conda environments, install a ``Python (myenv)`` Kernel in a first
environment:

.. sourcecode:: bash

    source activate myenv
    python -m ipykernel install --user --name myenv --display-name "Python (myenv)"

And in a second environment, after making sure ipykernel is installed in it:

.. sourcecode:: bash

    source activate other-env
    python -m ipykernel install --user --name other-env --display-name "Python (other-env)"

The ``--name`` value is used by Jupyter internally. These commands will overwrite
any existing kernel with the same name. ``--display-name`` is what you see in
the notebook menus.

Using virtualenv or inside a conda env, you can make your IPython kernel in
one env available to Jupyter in a different env.

To do so, run ``ipykernel install`` from the kernel's env, with --prefix pointing
to the Jupyter env:

.. sourcecode:: bash

    /path/to/kernel/env/bin/python -m ipykernel install --prefix=/path/to/jupyter/env --name 'python-my-env'

Note that this command will create a new configuration for the kernel in one
of the preferred location (see ``jupyter --paths`` command for more details):

* system-wide (e.g. /usr/local/share),
* in Jupyter's env (sys.prefix/share),
* per-user (~/.local/share or ~/Library/share)

If you want to edit the kernelspec before installing it, you can do so in two steps.
First, ask IPython to write its spec to a temporary location:

.. sourcecode:: bash

    ipython kernel install --prefix /tmp

Edit the files in /tmp/share/jupyter/kernels/python3 to your liking,
then when you are ready, tell Jupyter to install it (this will copy the files
into a place Jupyter will look):

.. sourcecode:: bash

    jupyter kernelspec install /tmp/share/jupyter/kernels/python3
