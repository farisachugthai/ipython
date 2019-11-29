"""
IPython: tools for interactive and parallel computing in Python.

https://ipython.org

**Python version check**
This check is also made in IPython/__init__, don't forget to update both when
changing Python version requirements.

From setup.py::

    >>> if sys.version_info < (3, 5):
        >>> pip_message = 'This may be due to an out of date pip. Make sure you have pip >= 9.0.1.'
        >>> try:
            >>> import pip
            >>> pip_version = tuple([int(x) for x in pip.__version__.split('.')[:3]])
            >>> if pip_version < (9, 0, 1):
                >>> pip_message = 'Your pip version is out of date, please install pip >= 9.0.1. '\
                >>> 'pip {} detected.'.format(pip.__version__)
            >>> else:
                >>> # pip is new enough - it must be something else
                >>> pip_message = ''
        >>> except Exception:
            >>> pass
        >>> error =


IPython 7.0+ supports Python 3.5 and above.
When using Python 2.7, please install IPython 5.x LTS Long Term Support version.
Python 3.3 and 3.4 were supported up to IPython 6.x.


See IPython `README.rst`_ file for more information:

.. _README.rst: https://github.com/ipython/ipython/blob/master/README.rst


Python {py} detected.
{pip}
.format(py=sys.version_info, pip=pip_message)

print(error, file=sys.stderr)
sys.exit(1)

"""
# -----------------------------------------------------------------------------
#  Copyright (c) 2008-2011, IPython Development Team.
#  Copyright (c) 2001-2007, Fernando Perez <fernando.perez@colorado.edu>
#  Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
#  Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import os
import sys

from .core import release
# from .core.interactiveshell import InteractiveShell  # noqa F0401
# from .terminal.embed import embed  # noqa F0401

# -----------------------------------------------------------------------------
# Setup everything
# -----------------------------------------------------------------------------

# Don't forget to also update setup.py when this changes!
if sys.version_info < (3, 6):
    raise ImportError("""
IPython 7.10+ supports Python 3.6 and above.
When using Python 2.7, please install IPython 5.x LTS Long Term Support
version. Python 3.3 and 3.4 were supported up to IPython 6.x.
Python 3.5 was supported with IPython 7.0 to 7.9.

See IPython `README.rst` file for more information:

    https://github.com/ipython/ipython/blob/master/README.rst

""")

# -----------------------------------------------------------------------------
# Setup the top level names
# -----------------------------------------------------------------------------

# Release data
__author__ = '%s <%s>' % (release.author, release.author_email)
__license__ = release.license
__version__ = release.version
version_info = release.version_info


def embed_kernel(module=None, local_ns=None, **kwargs):
    """Embed and start an IPython kernel in a given scope.

    If you don't want the kernel to initialize the namespace
    from the scope of the surrounding function,
    and/or you want to load full IPython configuration,
    you probably want `IPython.start_kernel()` instead.

    Parameters
    ----------
    module : types.ModuleType, optional
        The module to load into IPython globals (default: caller)
    local_ns : dict, optional
        The namespace to load into IPython user namespace (default: caller)

    kwargs : various, optional
        Further keyword args are relayed to the IPKernelApp constructor,
        allowing configuration of the Kernel.  Will only have an effect
        on the first embed_kernel call for a given process.

    """
    from .utils.frame import extract_module_locals

    (caller_module, caller_locals) = extract_module_locals(1)
    if module is None:
        module = caller_module
    if local_ns is None:
        local_ns = caller_locals

    # Only import .zmq when we really need it
    from ipykernel.embed import embed_kernel as real_embed_kernel
    real_embed_kernel(module=module, local_ns=local_ns, **kwargs)


def start_ipython(argv=None, **kwargs):
    """Launch an interactive IPython instance (as opposed to embedded).

    `IPython.embed` puts a shell in a particular calling scope,
    such as a function or method for debugging purposes,
    which is often not desirable.

    `start_ipython` does full, regular IPython initialization,
    including loading startup files, configuration, etc.
    much of which is skipped by `embed`.

    This is a public API method, and will survive implementation changes.

    However can I just change the part where it relies on an alias FFS?

    Parameters
    ----------
    argv : list or None, optional
        If unspecified or None, IPython will parse command-line options
        from sys.argv.
        To prevent any command-line parsing, pass an empty list: `argv=[]`.
    user_ns : dict, optional
        Specify this dictionary to initialize the IPython user namespace
        with particular values.
    ``**kwargs`` : dict, optional
        Any other kwargs will be passed to the Application constructor,
        such as `config`.

    """
    from IPython.terminal.ipapp import launch_new_instance
    return launch_new_instance(argv, **kwargs)


def start_kernel(argv=None, **kwargs):
    """Launch a normal IPython kernel instance (as opposed to embedded).

    `IPython.embed_kernel()` puts a shell in a particular calling scope,
    such as a function or method for debugging purposes,
    which is often not desirable.

    `start_kernel()` does full, regular IPython initialization,
    including loading startup files, configuration, etc.
    much of which is skipped by `embed()`.

    Parameters
    ----------
    argv : list, optional
        If unspecified or `None`, IPython will parse command-line options
        from `sys.argv`.
        To prevent any command-line parsing, pass an empty list: `argv=[]`.
    user_ns : dict, optional
        Specify this dictionary to initialize the IPython user namespace
        with particular values.
    ``**kwargs`` : dict, optional
        Any other kwargs will be passed to the Application constructor,
        such as `config`.

    """
    from IPython.kernel.zmq.kernelapp import launch_new_instance
    return launch_new_instance(argv=argv, **kwargs)
