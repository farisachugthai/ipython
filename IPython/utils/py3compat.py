# coding: utf-8
"""Compatibility tricks for Python 3. Mainly to do with unicode.

This file is deprecated and will be removed in a future version.
"""
import builtins as builtin_mod
import functools
import os
import platform
import re
import shutil
import types
from codecs import decode, encode
from sys import getfilesystemencoding

DEFAULT_ENCODING = getfilesystemencoding()
# from .encoding import DEFAULT_ENCODING

# keep reference to builtin_mod because the kernel overrides that value
# to forward requests to a frontend.
builtin_mod_name = "builtins"

which = shutil.which

getcwd = os.getcwd
MethodType = types.MethodType
# Refactor print statements in doctests.
_print_statement_re = re.compile(r"\bprint (?P<expr>.*)$", re.MULTILINE)
xrange = range
PY3 = True
PY2 = not PY3
PYPY = platform.python_implementation() == "PyPy"


def no_code(x, encoding=None):
    return x


str_to_unicode = no_code
unicode_to_str = no_code
cast_bytes_py2 = no_code
cast_unicode_py2 = no_code
buffer_to_bytes_py2 = no_code


def cast_unicode(s, encoding=None):
    """

    Parameters
    ----------
    s :
    encoding :

    Returns
    -------

    """
    if isinstance(s, bytes):
        return decode(s, encoding)
    return s


def cast_bytes(s, encoding=None):
    """

    Parameters
    ----------
    s :
    encoding :

    Returns
    -------

    """
    if not isinstance(s, bytes):
        return encode(s, encoding)
    return s


def buffer_to_bytes(buf):
    """Cast a buffer object to bytes"""
    if not isinstance(buf, bytes):
        buf = bytes(buf)
    return buf


def _modify_str_or_docstring(str_change_func):
    @functools.wraps(str_change_func)
    def wrapper(func_or_str):
        """

        Parameters
        ----------
        func_or_str :

        Returns
        -------

        """
        if isinstance(func_or_str, (str,)):
            func = None
            doc = func_or_str
        else:
            func = func_or_str
            doc = func.__doc__

        # PYTHONOPTIMIZE=2 strips docstrings, so they can disappear
        # unexpectedly
        if doc is not None:
            doc = str_change_func(doc)

        if func:
            func.__doc__ = doc
            return func
        return doc

    return wrapper


def safe_unicode(e):
    """unicode(e) with various fallbacks. Used for exceptions, which may not be
    safe to call unicode() on.
    """
    try:
        return str(e)
    except UnicodeError:
        pass

    try:
        return repr(e)
    except UnicodeError:
        pass

    return u"Unrecoverably corrupt evalue"


def input(prompt=""):
    """

    Parameters
    ----------
    prompt :

    Returns
    -------

    """
    return builtin_mod.input(prompt)


def isidentifier(s, dotted=False):
    """

    Parameters
    ----------
    s :
    dotted :

    Returns
    -------

    """
    if dotted:
        return all(isidentifier(a) for a in s.split("."))
    return s.isidentifier()


def iteritems(d):
    """

    Parameters
    ----------
    d :

    Returns
    -------

    """
    return iter(d.items())


def itervalues(d):
    """

    Parameters
    ----------
    d :

    Returns
    -------

    """
    return iter(d.values())


def execfile(fname, glob, loc=None, compiler=None):
    """Suggeston. Change fname in the last line to '<string>'.

    Parameters
    ----------
    fname :
    glob :
    loc :
    compiler :
    """
    loc = loc if (loc is not None) else glob
    with open(fname, "rb") as f:
        compiler = compiler or compile
        exec(compiler(f.read(), fname, "exec"), glob, loc)


def _print_statement_sub(match):
    expr = match.groups("expr")
    return "print(%s)" % expr


# Abstract u'abc' syntax:
@_modify_str_or_docstring
def u_format(s):
    """"{u}'abc'" --> "'abc'" (Python 3)

    Accepts a string or a function, so it can be used as a decorator."""
    return s.format(u="")


def get_closure(f):
    """Get a function's closure attribute"""
    return f.__closure__


def annotate(**kwargs):
    """Python 3 compatible function annotation for Python 2."""
    if not kwargs:
        raise ValueError("annotations must be provided as keyword arguments")

    def dec(f):
        """

        Parameters
        ----------
        f :

        Returns
        -------

        """
        if hasattr(f, "__annotations__"):
            for k, v in kwargs.items():
                f.__annotations__[k] = v
        else:
            f.__annotations__ = kwargs
        return f

    return dec
