"""Find files and directories which IPython uses.

So the todo for this module is that I think the py3compat family of functions
are pending deprecation.
"""
from importlib import import_module
import os.path
import shutil
import sys
import tempfile
from warnings import warn

import IPython
from IPython.utils.path import (get_home_dir, get_xdg_dir, get_xdg_cache_dir,
                                compress_user, _writable_dir, ensure_dir_exists)


def get_ipython_dir():
    """Get the IPython directory for this platform and user.

    This uses the logic in `get_home_dir` to find the home directory
    and then adds .ipython to the end of the path.
    """
    env = os.environ.copy()
    pjoin = os.path.join

    ipdir_def = '.ipython'

    home_dir = get_home_dir()
    xdg_dir = get_xdg_dir()

    if 'IPYTHON_DIR' in env:
        warn('The environment variable IPYTHON_DIR is deprecated. '
             'Please use IPYTHONDIR instead.')
    ipdir = env.get('IPYTHONDIR', env.get('IPYTHON_DIR', None))
    if ipdir is None:
        # not set explicitly, use ~/.ipython
        ipdir = pjoin(home_dir, ipdir_def)
        if xdg_dir:
            # Several IPython versions (up to 1.x) defaulted to .config/ipython
            # on Linux. We have decided to go back to using .ipython everywhere
            xdg_ipdir = pjoin(xdg_dir, 'ipython')

            if _writable_dir(xdg_ipdir):
                cu = compress_user
                if os.path.exists(ipdir):
                    warn(('Ignoring {0} in favour of {1}. Remove {0} to '
                          'get rid of this message').format(
                              cu(xdg_ipdir), cu(ipdir)))
                elif os.path.islink(xdg_ipdir):
                    warn(('{0} is deprecated. Move link to {1} to '
                          'get rid of this message').format(
                              # Dude look at this line of code.
                              # Are your abbreviations really helping or is it
                              # a shoddy way of circumventing how deeply
                              # nested the logic in these methods is???
                              cu(xdg_ipdir), cu(ipdir)))
                else:
                    warn('Moving {0} to {1}'.format(cu(xdg_ipdir), cu(ipdir)))
                    shutil.move(xdg_ipdir, ipdir)

    ipdir = os.path.normpath(os.path.expanduser(ipdir))
    if os.path.exists(ipdir) and not _writable_dir(ipdir):
        # ipdir exists, but is not writable
        # So wouldn't it be more logical to raise a PermissionsError?
        warn("IPython dir '{0}' is not a writable location,"
             " using a temp directory.".format(ipdir))
        ipdir = tempfile.mkdtemp()
    elif not os.path.exists(ipdir):
        parent = os.path.dirname(ipdir)
        if not _writable_dir(parent):
            # ipdir does not exist and parent isn't writable
            warn("IPython parent '{0}' is not a writable location,"
                 " using a temp directory.".format(parent))
            ipdir = tempfile.mkdtemp()

    return ipdir


def get_ipython_cache_dir():
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


def get_ipython_package_dir():
    """Get the base directory where IPython itself is installed."""
    # This was a weird time to not bother catching exceptions. check if IPython
    # has the file attr before working with it!
    if hasattr(IPython, '__file__'):
        return os.path.dirname(IPython.__file__)
    # else:


def get_ipython_module_path(module_str):
    """Find the path to an IPython module in this version of IPython.

    This will always find the version of the module that is in this importable
    IPython package. This will always return the path to the ``.py``
    version of the module.
    """
    if module_str == 'IPython':
        return os.path.join(get_ipython_package_dir(), '__init__.py')
    # I feel like the 3 lines below would do nicely in a function sprinkled
    # throughout a lot of this repo
    mod = import_module(module_str)
    the_path = mod.__file__.replace('.pyc', '.py')
    the_path = the_path.replace('.pyo', '.py')
    return the_path


def locate_profile(profile='default'):
    """Find the path to the folder associated with a given profile.

    I.E. find :envvar:`IPYTHONDIR`/profile_*.

    Raises
    ------
    :exc:`IOError`
        Why an IOError?
    """
    from IPython.core.profiledir import ProfileDir, ProfileDirError
    try:
        pd = ProfileDir.find_profile_dir_by_name(get_ipython_dir(), profile)
    except ProfileDirError:
        # IOError makes more sense when people are expecting a path
        raise IOError("Couldn't find profile %r" % profile)
    return pd.location
