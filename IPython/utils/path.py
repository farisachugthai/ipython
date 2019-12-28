# encoding: utf-8
"""Utilities for path handling.

Deleting filefind because it's copy pasted:

*) Here

*) Traitlets

*) ipython_genutils

Also of note.
There was a function wrapping 2 functions but it was all predicated on
Windows being installed.

So I deleted 2 of the functions and started the original function with.:

    if not sys.platform() == 'Windows':
        return

"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import errno
import glob
import logging
import os
import random
import shutil
import sys
from os import system
from pathlib import Path

# -----------------------------------------------------------------------------
# Code
# -----------------------------------------------------------------------------

logging.basicConfig()
fs_encoding = sys.getfilesystemencoding()


def _writable_dir(path):
    """Whether `path` is a directory, to which the user has write access."""
    return os.path.isdir(path) and os.access(path, os.W_OK)


def get_home_dir(require_writable=False):
    """Return the 'home' directory, as a unicode string using :mod:`pathlib`.

    Parameters
    ----------
    require_writable : bool, optional
        Default: False
        Do we need write permissions to :envvar:`HOME`?

    Returns
    -------
    home : str
        Path to your home dir

    """
    if not require_writable:
        return Path.home().__fspath__()
    else:
        if not _writable_dir(Path.home().__fspath__()):
            raise
        else:
            return Path.home().__fspath__()


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
        path = "~" + path[len(home) :]
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
    force_win32 : bool, optional
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
        Now the functions only 8 lines! *And 30 lines of docstring.* Aren't
        I the worst?

    """
    path_name = Path(name).expanduser()
    # Don't forget to check for cases where we get passed a Path.
    name = str(name)
    if path_name.is_file():
        return name
    if path_name.stem != ".py":
        name = Path(name + ".py")
        get_py_filename(name)
    else:
        raise OSError("File `%r` not found." % name)


def get_xdg_dir():
    """Checks for the user's config dir as defined by the XDG standard.

    First, we check for the presence of the env var XDG_CONFIG_HOME.
    This also checks for the existence of the directory even if the env var
    isn't defined, and checks whether that directory is writable.

    Returns
    -------
    Return the :envvar:`XDG_CONFIG_HOME`.

    """
    xdg = os.environ.get("XDG_CONFIG_HOME", None) or str(
        Path.home().joinpath(".config")
    )
    if xdg and _writable_dir(xdg):
        return xdg


def get_xdg_cache_dir():
    """Return the XDG_CACHE_HOME, if it is defined and exists, else None.

    This is only for non-OS X posix (Linux,Unix,etc.) systems.
    Why? I defined XDG_CACHE_HOME on my windows OS it's not like we're
    incapable of doing so?
    """
    xdg = os.environ.get("XDG_CACHE_HOME", None) or str(Path.home().joinpath(".cache"))
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

    def unescape(s):
        for pattern in "*[]!?":
            s = s.replace(r"\{0}".format(pattern), pattern)
        return s

    return "\\".join(map(unescape, s.split("\\\\")))


def shellglob(args):
    """Do glob expansion for each element in `args` and return a flattened list.
    """
    expanded = []
    for a in args:
        expanded.extend(Path(a).glob('*'))
    return expanded


def target_outdated(target, deps):
    """Determine whether a target is out of date.

    target_outdated(target,deps) -> 1/0

    deps: list of filenames which MUST exist.
    target: single filename which may or may not exist.

    If target doesn't exist or is older than any file listed in deps, return
    true, otherwise return false.

    """
    try:
        target_time = os.path.getmtime(target)
    except OSError:
        return True
    for dep in deps:
        dep_time = os.path.getmtime(dep)
        if dep_time > target_time:
            logging.debug("For target", target, "Dep failed:", dep)
            logging.debug("times (dep,tar):", dep_time, target_time)
            return True


def target_update(target, deps, cmd):
    """Update a target with a given command given a list of dependencies.

    target_update(target,deps,cmd) -> runs cmd if target is outdated.

    This is just a wrapper around target_outdated() which calls the given
    command if target is outdated.
    """
    if target_outdated(target, deps):
        system(cmd)


def link(src, dst):
    """Create a hard link ``src`` to ``dst``, returning 0 or errno.

    .. note:: Special :mod:`errno` ``ENOLINK`` will be returned if ``os.link``
              isn't supported by the operating system. This is true on Android.

    Parameters
    ----------
    src :
    dst :

    """
    ENOLINK = 1998

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
    elif link_errno:
        # Either link isn't supported, or the filesystem doesn't support
        # linking, or 'src' and 'dst' are on different filesystems.
        shutil.copy(src, dst)


def ensure_dir_exists(path, mode=0o755):
    """Ensure that a directory exists.

    If it doesn't exist, try to create it and protect against a race condition
    if another process is doing the same.

    If it already exists, then move along.

    Raises
    ------
    PermissionError
    OSError

    """
    pathlib_path = Path(path)
    if not pathlib_path.exists():
        try:
            pathlib_path.mkdir(path, mode)
        except FileExistsError:
            pass
        except PermissionError:
            raise
        except OSError:
            raise
    elif not pathlib_path.is_dir():
        raise FileExistsError('File already exists: %s', path)
