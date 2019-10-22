.. _install_index:

============
Installation
============

.. toctree:: Installation
   :maxdepth: 1

   install
   kernel_install


This section will guide you through :ref:`installing IPython itself <install>`,
and installing :ref:`kernels for Jupyter <kernel_install>` if you wish to
work with multiple version of Python, or you're working in
multiple environments.


Quick install reminder
~~~~~~~~~~~~~~~~~~~~~~

To install IPython, open your console of choice, and run the following.
This assumes a working installation of python is available:

.. code-block:: bash

    $ pip install ipython

Install and register an IPython kernel with Jupyter:

.. code-block:: bash

    $ python -m pip install ipykernel

    $ python -m ipykernel install [--user] [--name <machine-readable-name>] [--display-name <"User Friendly Name">]

.. caution:: Python versions

   The above commands assume that python points to python3. It may be necessary
   to specify which version of python in the case that there are multiple
   available on the $PATH.

For more help see

.. code-block:: bash

    $ python -m ipykernel install  --help


.. seealso::

   `Installing Jupyter <http://jupyter.readthedocs.io/en/latest/install.html>`__
     The Notebook, nbconvert, and many other former pieces of IPython are now
     part of Project Jupyter.


TroubleShooting

If you are encountering this error message you are likely trying to install or
use IPython from source. You need to checkout the remote 5.x branch. If you are
using git the following should work::

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
