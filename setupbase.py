# encoding: utf-8
"""
This module defines the things that are used in setup.py for building IPython

This includes:

    * The basic arguments to setup
    * Functions for finding things like packages, package data, etc.
    * A function for checking dependencies.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import logging
import re
import os
import sys
from glob import glob
from logging import log

# from distutils import log
# from distutils.command.build_py import build_py
from setuptools.command.build_py import build_py
# What is the replacement for this?
from distutils.command.build_scripts import build_scripts
from setuptools.command.install import install
# from distutils.command.install import install
from setuptools.command.install_scripts import install_scripts
# from distutils.command.install_scripts import install_scripts
from setuptools import Command
# from distutils.cmd import Command
from distutils.command.install_data import install_data
from distutils.util import change_root, convert_path

# -------------------------------------------------------------------------------
# Useful globals and utility functions
# -------------------------------------------------------------------------------

# A few handy globals
isfile = os.path.isfile
pjoin = os.path.join
repo_root = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig()


def execfile(fname, globs, locs=None):
    locs = locs or globs
    with open(fname) as f:
        exec(compile(f.read(), fname, "exec"), globs, locs)

# A little utility we'll need below, since glob() does NOT allow you to do
# exclusion on multiple endings!


def file_doesnt_endwith(test, endings):
    """Return true if test is a file and its name does NOT end with any
    of the strings listed in endings."""
    if not isfile(test):
        return False
    for e in endings:
        if test.endswith(e):
            return False
    return True

# Setupext

class install_data_ext(install_data):

    def initialize_options(self):
        self.install_base = None
        self.install_platbase = None
        self.install_purelib = None
        self.install_headers = None
        self.install_lib = None
        self.install_scripts = None
        self.install_data = None

        self.outfiles = []
        self.root = None
        self.force = 0
        self.data_files = self.distribution.data_files
        self.warn_dir = 1


    def finalize_options(self):
        self.set_undefined_options('install',
                                   ('root', 'root'),
                                   ('force', 'force'),
                                   ('install_base', 'install_base'),
                                   ('install_platbase',
                                    'install_platbase'),
                                   ('install_purelib',
                                    'install_purelib'),
                                   ('install_headers',
                                    'install_headers'),
                                   ('install_lib', 'install_lib'),
                                   ('install_scripts',
                                    'install_scripts'),
                                   ('install_data', 'install_data'))


    def run(self):
        """
        This is where the meat is.  Basically the data_files list must
        now be a list of tuples of 3 entries.  The first
        entry is one of 'base', 'platbase', etc, which indicates which
        base to install from.  The second entry is the path to install
        too.  The third entry is a list of files to install.
        """
        for lof in self.data_files:
            if lof[0]:
                base = getattr(self, 'install_' + lof[0])
            else:
                base = getattr(self, 'install_base')
            dir = convert_path(lof[1])
            if not os.path.isabs(dir):
                dir = os.path.join(base, dir)
            elif self.root:
                dir = change_root(self.root, dir)
            self.mkpath(dir)

            files = lof[2]
            if len(files) == 0:
                # If there are no files listed, the user must be
                # trying to create an empty directory, so add the
                # directory to the list of output files.
                self.outfiles.append(dir)
            else:
                # Copy files, adding them to the list of output files.
                for f in files:
                    f = convert_path(f)
                    (out, _) = self.copy_file(f, dir)
                    #print "DEBUG: ", out  # dbg
                    self.outfiles.append(out)


        return self.outfiles

# ---------------------------------------------------------------------------
# Basic project information
# ---------------------------------------------------------------------------


# release.py contains version, authors, license, url, keywords, etc.
execfile(pjoin(repo_root, 'IPython', 'core', 'release.py'), globals())

# Create a dict with the basic information
# This dict is eventually passed to setup after additional keys are added.
setup_args = dict(
      name=name,
      version=version,
      description=description,
      long_description=long_description,
      author=author,
      author_email=author_email,
      url=url,
      license=license,
      platforms=platforms,
      keywords=keywords,
      classifiers=classifiers,
      cmdclass={'install_data': install_data_ext},
      project_urls={
          'Documentation': 'https://ipython.readthedocs.io/',
          'Funding': 'https://numfocus.org/',
          'Source': 'https://github.com/ipython/ipython',
          'Tracker': 'https://github.com/ipython/ipython/issues',
      }
      )


# ---------------------------------------------------------------------------
# Find package data
# ---------------------------------------------------------------------------


def find_package_data():
    """
    Find IPython's package_data.
    """
    # This is not enough for these things to appear in an sdist.
    # We need to muck with the MANIFEST to get this to work

    package_data = {
        'IPython.core': ['profile/README*'],
        'IPython.core.tests': ['*.png', '*.jpg', 'daft_extension/*.py'],
        'IPython.lib.tests': ['*.wav'],
        'IPython.testing.plugin': ['*.txt'],
    }

    return package_data


def check_package_data(package_data):
    """verify that package_data globs make sense"""
    print("checking package data")
    for pkg, data in package_data.items():
        pkg_root = pjoin(*pkg.split('.'))
        for d in data:
            path = pjoin(pkg_root, d)
            if '*' in path:
                assert len(glob(path)) > 0, "No files match pattern %s" % path
            else:
                assert os.path.exists(path), "Missing package data: %s" % path


def check_package_data_first(command):
    """decorator for checking package_data before running a given command

    Probably only needs to wrap build_py
    """
    class DecoratedCommand(command):
        def run(self):
            check_package_data(self.package_data)
            command.run(self)
    return DecoratedCommand


# ---------------------------------------------------------------------------
# Find data files
# ---------------------------------------------------------------------------

def find_data_files():
    """
    Find IPython's data_files.

    Just man pages at this point.
    """

    if "freebsd" in sys.platform:
        manpagebase = pjoin('man', 'man1')
    else:
        manpagebase = pjoin('share', 'man', 'man1')

    # Simple file lists can be made by hand
    manpages = [f for f in glob(pjoin('docs', 'man', '*.1.gz')) if isfile(f)]
    if not manpages:
        # When running from a source tree, the manpages aren't gzipped
        manpages = [f for f in glob(pjoin('docs', 'man', '*.1')) if isfile(f)]

    # And assemble the entire output list
    data_files = [(manpagebase, manpages)]

    return data_files


# The two functions below are copied from IPython.utils.path, so we don't need
# to import IPython during setup, which fails on Python 3.

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
    except os.error:
        return 1
    for dep in deps:
        dep_time = os.path.getmtime(dep)
        if dep_time > target_time:
            # print "For target",target,"Dep failed:",dep # dbg
            # print "times (dep,tar):",dep_time,target_time # dbg
            return 1
    return 0


def target_update(target, deps, cmd):
    """Update a target with a given command given a list of dependencies.

    target_update(target,deps,cmd) -> runs cmd if target is outdated.

    This is just a wrapper around target_outdated() which calls the given
    command if target is outdated."""

    if target_outdated(target, deps):
        os.system(cmd)

# ---------------------------------------------------------------------------
# Find scripts
# ---------------------------------------------------------------------------


def find_entry_points():
    """Defines the command line entry points for IPython

    This always uses setuptools-style entry points. When setuptools is not in
    use, our own build_scripts_entrypt class below parses these and builds
    command line scripts.

    Each of our entry points gets both a plain name, e.g. ipython, and one
    suffixed with the Python major version number, e.g. ipython3.
    """
    ep = [
            'ipython%s = IPython:start_ipython',
            'iptest%s = IPython.testing.iptestcontroller:main',
        ]
    suffix = str(sys.version_info[0])
    return [e % '' for e in ep] + [e % suffix for e in ep]


script_src = """#!{executable}
# This script was automatically generated by setup.py
if __name__ == '__main__':
    from {mod} import {func}
    {func}()
"""


class build_scripts_entrypt(build_scripts):
    """Build the command line scripts

    Parse setuptools style entry points and write simple scripts to run the
    target functions.

    On Windows, this also creates .cmd wrappers for the scripts so that you can
    easily launch them from a command line.
    """

    def run(self):
        self.mkpath(self.build_dir)
        outfiles = []
        for script in find_entry_points():
            name, entrypt = script.split('=')
            name = name.strip()
            entrypt = entrypt.strip()
            outfile = os.path.join(self.build_dir, name)
            outfiles.append(outfile)
            print('Writing script to', outfile)

            mod, func = entrypt.split(':')
            with open(outfile, 'w') as f:
                f.write(script_src.format(executable=sys.executable,
                                          mod=mod, func=func))

            if sys.platform == 'win32':
                # Write .cmd wrappers for Windows so 'ipython' etc. work at the
                # command line
                cmd_file = os.path.join(self.build_dir, name + '.cmd')
                cmd = r'@"{python}" "%~dp0\{script}" %*\r\n'.format(
                        python=sys.executable, script=name)
                log.info("Writing %s wrapper script" % cmd_file)
                with open(cmd_file, 'w') as f:
                    f.write(cmd)

        return outfiles, outfiles


class install_lib_symlink(Command):
    user_options = [
        ('install-dir=', 'd', "directory to install to"),
        ]

    def initialize_options(self):
        self.install_dir = None

    def finalize_options(self):
        self.set_undefined_options('symlink',
                                   ('install_lib', 'install_dir'),
                                   )

    def run(self):
        if sys.platform == 'win32':
            raise Exception("This doesn't work on Windows.")
        pkg = os.path.join(os.getcwd(), 'IPython')
        dest = os.path.join(self.install_dir, 'IPython')
        if os.path.islink(dest):
            print('removing existing symlink at %s' % dest)
            os.unlink(dest)
        print('symlinking %s -> %s' % (pkg, dest))
        os.symlink(pkg, dest)


class unsymlink(install):
    def run(self):
        dest = os.path.join(self.install_lib, 'IPython')
        if os.path.islink(dest):
            print('removing symlink at %s' % dest)
            os.unlink(dest)
        else:
            print('No symlink exists at %s' % dest)


class install_symlinked(install):
    def run(self):
        if sys.platform == 'win32':
            raise Exception("This doesn't work on Windows.")

        # Run all sub-commands (at least those that need to be run)
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)

    # 'sub_commands': a list of commands this command might have to run to
    # get its work done.  See cmd.py for more info.
    sub_commands = [('install_lib_symlink', lambda self:True),
                    ('install_scripts_sym', lambda self:True),
                    ]


class install_scripts_for_symlink(install_scripts):
    """Redefined to get options from 'symlink' instead of 'install'.

    I love distutils almost as much as I love setuptools.
    """

    def finalize_options(self):
        self.set_undefined_options('build', ('build_scripts', 'build_dir'))
        self.set_undefined_options('symlink',
                                   ('install_scripts', 'install_dir'),
                                   ('force', 'force'),
                                   ('skip_build', 'skip_build'),
                                   )


# ---------------------------------------------------------------------------
# VCS related
# ---------------------------------------------------------------------------


def git_prebuild(pkg_dir, build_cmd=build_py):
    """Return extended build or sdist command class for recording commit

    records git commit in IPython.utils._sysinfo.commit

    for use in IPython.utils.sysinfo.sys_info() calls after installation.
    """

    class MyBuildPy(build_cmd):
        ''' Subclass to write commit data into installation tree '''

        def run(self):
            # loose as `.dev` is suppose to be invalid
            print("check version number")
            loose_pep440re = re.compile(r'^(\d+)\.(\d+)\.(\d+((a|b|rc)\d+)?)(\.post\d+)?(\.dev\d*)?$')
            if not loose_pep440re.match(version):
                raise ValueError(
                    "Version number '%s' is not valid (should match [N!]N(.N)*[{a|b|rc}N][.postN][.devN])" % version)

            build_cmd.run(self)
            # this one will only fire for build commands
            if hasattr(self, 'build_lib'):
                self._record_commit(self.build_lib)

        def make_release_tree(self, base_dir, files):
            # this one will fire for sdist
            build_cmd.make_release_tree(self, base_dir, files)
            self._record_commit(base_dir)

        def _record_commit(self, base_dir):
            import subprocess
            proc = subprocess.Popen('git rev-parse --short HEAD',
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
            repo_commit, _ = proc.communicate()
            repo_commit = repo_commit.strip().decode("ascii")

            out_pth = pjoin(base_dir, pkg_dir, 'utils', '_sysinfo.py')
            if os.path.isfile(out_pth) and not repo_commit:
                # nothing to write, don't clobber
                return

            print("writing git commit '%s' to %s" % (repo_commit, out_pth))

            # remove to avoid overwriting original via hard link
            try:
                os.remove(out_pth)
            except (IOError, OSError):
                pass
            with open(out_pth, 'w') as out_file:
                out_file.writelines([
                    '# GENERATED BY setup.py\n',
                    'commit = u"%s"\n' % repo_commit,
                ])
    return MyBuildPy
