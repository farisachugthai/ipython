# encoding: utf-8
"""Utilities for path handling.

The lack of :mod:`pathlib` usage is a perfect sign of the age of this module.

Also I'm deleting filefind because it's copy pasted:

*) Here

*) Traitlets

*) ipython_genutils

Here's the old docstring.

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

    .. todo:: Is this in traitlets now?

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


Also worth pointing out I got rid of a bunch of absurd logic in this file.
There was a functon wrapping 2 functions but it was all predicated on
Windows being installed.

So I deleted 2 of the functions and started the original function with.:

    if not sys.platform() == 'Windows':
        return

"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import errno
import glob
import os
from pathlib import Path
import random
import shutil
import sys
from warnings import warn

from ipython_genutils.path import filefind
from IPython.utils.process import system

# -----------------------------------------------------------------------------
# Code
# -----------------------------------------------------------------------------


def _writable_dir(path):
    """Whether `path` is a directory, to which the user has write access."""
    return os.path.isdir(path) and os.access(path, os.W_OK)


def get_long_path_name(path):
    """Expand a path into its long form.

    On Windows this expands any ~ in the paths using ctypes.
    On other platforms, it is a null operation.

    Parameters
    ----------
    path : str (path-like)
        Path to perform a tilde "compression" on.

    Returns
    -------
    str (path-like)
        Path with a tilde added.

    Raises
    ------
    :exc:`ImportError`
        If ctypes isn't installed.
    :exc:`OSError`
        If ctypes doesn't have windll.

    Examples
    --------
    >>> get_long_path_name('c:\\docume~1')
    'c:\\\\Documents and Settings'
    """
    if not sys.platform == "win32":
        return

    try:
        import ctypes
    except ImportError:
        raise ImportError("you need to have ctypes installed for this to work")
    if not getattr(ctypes, "windll", None):
        raise OSError("Ctypes doesn't have WinDLL available.")

    _GetLongPathName = ctypes.windll.kernel32.GetLongPathNameW
    _GetLongPathName.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]

    buf = ctypes.create_unicode_buffer(260)
    rv = _GetLongPathName(path, buf, 260)
    if rv == 0 or rv > 260:
        return path
    else:
        return buf.value


def compress_user(path):
    """Reverse of :func:`os.path.expanduser`.

    Parameters
    ----------
    path : str (path-like)
        Path to perform a tilde "compression" on.

    Returns
    -------
    str (path-like)
        Path with a tilde added.

    """
    home = os.path.expanduser("~")
    if path.startswith(home):
        path = "~" + path[len(home):]
    return path


def get_py_filename(name, force_win32=None):
    """Return a valid python filename in the current directory.

    If the given name is not a file, it adds '.py' and searches again.

    .. note::
        This function is used by the `%edit` magic. So pretty important.

    Parameters
    ----------
    name : str (os.Pathlike)
        Path to find.
    force_win32 : bool
        Not used anymore

    Returns
    -------
    name : str (path-like)
        Path with a tilde added.

    Raises
    ------
    :exc:`OSError`
        With an informative message if the file isn't found.

    .. versionchanged:: 7.11.0.dev. Changed everything.

        Uses pathlib instead of os.path.
        IOError tmk got deprecated so raise OSError.
        Is also recursive because that was an interesting way to do it IMO.
        Now the functions only 4 lines! *And 30 lines of docstring. Aren't
        I the worst?

    """
    name = Path(name).expanduser()
    if name.is_file():
        return str(name)
    if name.stem != ".py":
        name = Path(name + ".py")
        get_py_filename(name)
    else:
        raise OSError("File `%r` not found." % name)


def get_home_dir(require_writable=False):
    """Return the 'home' directory, as a unicode string using pathlib.

    Parameters
    ----------
    require_writable : bool
        [default: False]

    Returns
    -------
    Path to your home dir
    """
    if require_writable:
        print("utils.path:get_home_dir Hey fix the function calling this.")
    return Path.home().__fspath__()


def get_xdg_dir():
    """Return the XDG_CONFIG_HOME, if it is defined and exists, else None."""
    env = os.environ
    xdg = env.get("XDG_CONFIG_HOME", None) or os.path.join(get_home_dir(), ".config")
    if xdg and _writable_dir(xdg):
        return xdg


def get_xdg_cache_dir():
    """Return the XDG_CACHE_HOME, if it is defined and exists, else None.

    This is only for non-OS X posix (Linux,Unix,etc.) systems.
    Why? I defined XDG_CACHE_HOME on my windows OS it's not like we're
    incapable of doing so?
    """
    env = os.environ
    xdg = env.get("XDG_CACHE_HOME", None) or os.path.join(get_home_dir(), ".cache")
    if xdg and _writable_dir(xdg):
        return xdg


def expand_path(s):
    r"""Expand $VARS and ~names in a string, like a shell.

    Largely useful for Win32. On Unix this simply runs expanduser(expandvars(s)).

    Notes
    -----
    This is a pretty subtle hack. When expand user is given a UNC path
    on Windows (\\server\share$\%username%), os.path.expandvars, removes
    the $ to get (\\server\share\%username%). I think it considered $
    alone an empty var. But, we need the $ to remains there (it indicates
    a hidden share).

    Examples
    --------
    .. ipython::

       In [2]: os.environ['FOO']='test'

       In [3]: expand_path('variable FOO is $FOO')
       Out[3]: 'variable FOO is test'

    """
    if os.name == "nt":
        s = s.replace("$\\", "IPYTHON_TEMP")
    s = os.path.expandvars(os.path.expanduser(s))
    if os.name == "nt":
        s = s.replace("IPYTHON_TEMP", "$\\")
    return s


def unescape_glob(s):
    """Unescape glob pattern in `string`. Dont use the word string wtf?"""
    for pattern in "*[]!?":
        s = s.replace(r"\{0}".format(pattern), pattern)

    return "\\".join(map(unescape, s.split("\\\\")))


def shellglob(args):
    """Do glob expansion for each element in `args` and return a flattened list.

    Unmatched glob pattern will remain as-is in the returned list.

    Pretty sure that this only exists to aide glob.glob in handling Windows
    paths.
    """
    expanded = []
    # Do not unescape backslash in Windows as it is interpreted as
    # path separator:
    unescape = unescape_glob if sys.platform != "win32" else lambda x: x
    for a in args:
        expanded.extend(glob.glob(a) or [unescape(a)])
    return expanded


def target_outdated(target, deps):
    """Determine whether a target is out of date.

    target_outdated(target,deps) -> 1/0

    deps: list of filenames which MUST exist.
    target: single filename which may or may not exist.

    If target doesn't exist or is older than any file listed in deps, return
    true, otherwise return false.

    .. warning:: THIS DOESN'T CATCH AN ERROR CORRECTLY LIKE GUIZE

        Original line: except os.error:

    Also wth why return 1 return True like a normal person.

    """
    try:
        target_time = os.path.getmtime(target)
    except OSError:
        return True
    for dep in deps:
        dep_time = os.path.getmtime(dep)
        if dep_time > target_time:
            # print "For target",target,"Dep failed:",dep # dbg
            # print "times (dep,tar):",dep_time,target_time # dbg
            return True


def target_update(target, deps, cmd):
    """Update a target with a given command given a list of dependencies.

    target_update(target,deps,cmd) -> runs cmd if target is outdated.

    This is just a wrapper around target_outdated() which calls the given
    command if target is outdated.
    """
    if target_outdated(target, deps):
        system(cmd)


ENOLINK = 1998


def link(src, dst):
    """Create a hard link ``src`` to ``dst``, returning 0 or errno.

    Note that the special errno ``ENOLINK`` will be returned if ``os.link``
    isn't supported by the operating system.
    """
    if not hasattr(os, "link"):
        return ENOLINK
    link_errno = 0
    try:
        os.link(src, dst)
    except OSError as e:
        link_errno = e.errno
    return link_errno


def link_or_copy(src, dst):
    """Attempt to hardlink ``src`` to ``dst``, copying if the link fails.

    Attempt to maintain the semantics of `shutil.copy`.

    Because `os.link` does not overwrite files, a unique temporary file
    will be used if the target already exists, then that file will be moved
    into place.
    """
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))

    link_errno = link(src, dst)
    if link_errno == errno.EEXIST:
        if os.stat(src).st_ino == os.stat(dst).st_ino:
            # dst is already a hard link to the correct file, so we don't need
            # to do anything else. If we try to link and rename the file
            # anyway, we get duplicate files - see
            # http://bugs.python.org/issue21876
            return

        new_dst = dst + "-temp-%04X" % (random.randint(1, 16 ** 4),)
        try:
            link_or_copy(src, new_dst)
        except BaseException:
            try:
                os.remove(new_dst)
            except OSError:
                pass
            raise
        os.rename(new_dst, dst)
    elif link_errno != 0:
        # Either link isn't supported, or the filesystem doesn't support
        # linking, or 'src' and 'dst' are on different filesystems.
        shutil.copy(src, dst)


def ensure_dir_exists(path, mode=0o755):
    """Ensure that a directory exists.

    If it doesn't exist, try to create it and protect against a race condition
    if another process is doing the same.

    The default permissions are 755, which differ from os.makedirs default of 777.

    Note
    ----
    All this fucking does is call os.makedirs() and raise a bunch of errors.
    This isn't very well implemented at all.
    """
    if not os.path.exists(path):
        try:
            os.makedirs(path, mode=mode)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    elif not os.path.isdir(path):
        raise IOError("%r exists but is not a directory" % path)
