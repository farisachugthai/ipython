"""Find files and directories which IPython uses.

So the todo for this module is that I think the py3compat family of functions
are pending deprecation.

Don't know how I didn't think of this. Don't let anything in utils.path
import from here. Circular imports.
"""
from importlib import import_module
import os
from pathlib import Path
import shutil
import sys
from warnings import warn

from IPython.utils.path import (
    get_xdg_dir,
    get_xdg_cache_dir,
    ensure_dir_exists,
)


def _writable_dir(path):
    """Whether `path` is a directory, to which the user has write access."""
    return os.path.isdir(path) and os.access(path, os.W_OK)


def get_ipython_dir() -> str:
    """Get the IPython directory for this platform and user.

    This uses the logic in `get_home_dir` to find the home directory
    and then adds .ipython to the end of the path.

    Oh now that I looked it over, it actually doesn't use the logic in get_home_dir.
    It actually duplicates almost all of the code in that module.

    Why doesn't it use the ProfileLocate class though?
    """
    home_dir = Path.home()
    ipdir = home_dir.joinpath(".ipython")
    xdg_dir = Path(get_xdg_dir())
    xdg_ipdir = xdg_dir.joinpath(".ipython")

    if os.environ.get("IPYTHON_DIR"):
        warn(
            "The environment variable IPYTHON_DIR is deprecated. "
            "Please use IPYTHONDIR instead."
        )

    if os.environ.get("IPYTHONDIR", os.environ.get("IPYTHON_DIR", None)):
        if _writable_dir(xdg_ipdir):
            deprecated_profile_warning(ipdir, xdg_dir)

    # Let's short-circuit this logic a little. Most people have their profiles in the spot we assume it's in
    # pathlib.Path.is_dir docs
    # False is also returned if the path doesn’t exist or is a broken
    # symlink; other errors(such as permission errors) are propagated.)
    if ipdir.is_dir():
        return ipdir.__fspath__()
    elif os.path.exists(ipdir) and not _writable_dir(ipdir):
        # ipdir exists, but is not writable
        # So wouldn't it be more logical to raise a PermissionsError?
        # Eh but i don't wanna crash the application. but this seems like the
        # right time to do so. TODO:
        raise PermissionError("{} is not a writable directory.".format(ipdir))

    if hasattr(ipdir, "__fspath__"):
        ipdir = ipdir.__fspath__()

    return ipdir


def deprecated_profile_warning(ipdir=None, xdg_ipdir=None):
    """TODO: When this gets refactored into/with ProfileLocate, you can
    easily remove the arguments as they should be bound as instance attributes.
    """
    if os.path.exists(ipdir):
        warn(
            (
                "Ignoring {0} in favour of {1}. Remove {0} to "
                "get rid of this message"
            ).format(xdg_ipdir, ipdir)
        )

    elif os.path.islink(xdg_ipdir):
        warn(
            (
                "{0} is deprecated. Move link to {1} to " "get rid of this message"
            ).format(xdg_ipdir, ipdir)
        )
    else:
        warn("Moving {0} to {1}".format(xdg_ipdir, ipdir))
        try_to_move(xdg_ipdir, ipdir)


def try_to_move(source, destination):
    """shutil.move with a try except if there's a problem."""
    try:
        shutil.move(source, destination)
    except (shutil.SameFileError, IsADirectoryError):
        warn(
            "Seems the destination already exists."
            "Please move manually to prevent future errors."
        )


def get_ipython_cache_dir() -> str:
    """Get the cache directory it is created if it does not exist."""
    xdgdir = get_xdg_cache_dir()
    if xdgdir is None:
        return get_ipython_dir()
    ipdir = os.path.join(xdgdir, "ipython")
    if not os.path.exists(ipdir) and _writable_dir(xdgdir):
        ensure_dir_exists(ipdir)
    elif not _writable_dir(xdgdir):
        return get_ipython_dir()

    return ipdir


def get_ipython_package_dir() -> str:
    """Get the base directory where IPython itself is installed."""
    # This was a weird time to not bother catching exceptions. check if IPython
    # has the file attr before working with it!
    # Wait i haven't imported it yet....
    import IPython

    if hasattr(IPython, "__file__"):
        return os.path.dirname(IPython.__file__)
    ipdir = os.path.dirname(IPython.__file__)
    return ipdir


def get_ipython_module_path(module_str=None):
    """Find the path to an IPython module in this version of IPython.

    This will always find the version of the module that is in this importable
    IPython package. This will always return the path to the ``.py``
    version of the module.
    """
    if not module_str:
        return
    if module_str == "IPython":
        return os.path.join(get_ipython_package_dir(), "__init__.py")
    # I feel like the 3 lines below would do nicely in a function sprinkled
    # throughout a lot of this repo
    mod = import_module(module_str)
    the_path = mod.__file__.replace(".pyc", ".py")
    the_path = the_path.replace(".pyo", ".py")
    return the_path


def locate_profile(profile="default"):
    """Find the path to the folder associated with a given profile.

    I.E. find :envvar:`IPYTHONDIR`/profile_*.

    .. versionchanged:: 7.11 -- Now raises an OSError.

    Raises
    ------
    :exc:`IOError`
        Why an IOError?
        They got deprecated.

    """
    from IPython.core.profiledir import ProfileDir, ProfileDirError

    try:
        pd = ProfileDir.find_profile_dir_by_name(get_ipython_dir(), profile)
    except ProfileDirError:
        raise OSError("Couldn't find profile %r" % profile)
    return pd.location
