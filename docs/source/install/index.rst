.. _install_index:

============
Installation
============

.. module:: install-index
   :synopsis: Root of installation instructions

.. toctree:: Installation
   :maxdepth: 2

   install
   kernel_install

This section will guide you through :ref:`installing IPython itself <install>`,
and installing :ref:`kernels for Jupyter <kernel_install>` if you wish to
work with multiple version of Python, or you're working in
multiple environments.

Troubleshooting
===============

.. admonition:: This troubleshooting guide is old.

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
one can refer to the output of ``pip uninstall``.:

.. code-block:: console-session

   python.exe -m pip uninstall [options] -r <requirements file> ...

   Description:
      Uninstall packages.

      pip is able to uninstall most installed packages. Known exceptions are:

   .. nested::

      - **Pure distutils packages installed with ``python setup.py install``, which
        leave behind no metadata to determine what files were installed.
      - Script wrappers installed by ``python setup.py develop``.**

