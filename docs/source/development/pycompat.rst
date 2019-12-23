:orphan:

Writing code for Python 2 and 3
===============================

.. commented out because the makefile gets it now
.. .. module:: IPython.utils.py3compat
   .. :synopsis: Python 2 & 3 compatibility helpers


IPython 6 requires Python 3, so our compatibility module
``IPython.utils.py3compat`` is deprecated and will be removed in a future
version. In most cases, we recommend you use the `six module
<https://pythonhosted.org/six/>`__ to support compatible code. This is widely
used by other projects, so it is familiar to many developers and thoroughly
battle-tested.

Our ``py3compat`` module provided some more specific unicode conversions than
those offered by ``six``. If you want to use these, copy them into your own code
from IPython 5.x. Do not rely on importing them from IPython, as the module may
be removed in the future.

.. seealso::

   `Porting Python 2 code to Python 3 <https://docs.python.org/3/howto/pyporting.html>`_
     Official information in the Python docs.

   `Python-Modernize <http://python-modernize.readthedocs.io/en/latest/>`_
     A tool which helps make code compatible with Python 3.

   `Python-Future <http://python-future.org/>`_
     Another compatibility tool, which focuses on writing code for Python 3 and
     making it work on Python 2.


Not related entirely but here's the old ``IPython.utils.path.filefind`` docstring.

.. currentmodule:: IPython.utils.path

.. function:: filefind

    This iterates through a sequence of paths looking for a file and returns
    the full, absolute path of the first occurrence of the file.  If no set of
    path dirs is given, the filename is tested as is, after running through
    :func:`expandvars` and :func:`expanduser`.  Thus a simple call::

        filefind('myfile.txt')

    will find the file in the current working dir, but::

        filefind('~/myfile.txt')

    Will find the file in the users home directory.  This function does not
    automatically try any paths, such as the cwd or the user's home directory.

Parameters
----------
filename : str
  The filename to look for.
path_dirs : str, None or sequence of str
  The sequence of paths to look for the file in.  If None, the filename
  need to be absolute or be in the cwd.  If a string, the string is
  put into a sequence and the searched.  If a sequence, walk through
  each element and join with ``filename``, calling :func:`expandvars`
  and :func:`expanduser` before testing for existence.

Returns
-------
Raises :exc:`IOError` or returns absolute path to file.
