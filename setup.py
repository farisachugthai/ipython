#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Setup script for IPython.

Under Posix environments it works like a typical setup.py script.
Under Windows, the command sdist is not supported, since IPython
requires utilities which are not available under Windows.


-----------------------------------------------------------------------------

  Copyright (c) 2008-2011, IPython Development Team.
  Copyright (c) 2001-2007, Fernando Perez <fernando.perez@colorado.edu>
  Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
  Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>

  Distributed under the terms of the Modified BSD License.

  The full license is in the file COPYING.rst, distributed with this software.

-----------------------------------------------------------------------------


It's also probably worth noting that in the dir
site-packages/ipython-7.8.0-dist-info/ is  file called entry_points.txt.

It only has the following for it's contents:

[console_scripts]

[pygments.lexers]
ipython = IPython.lib.lexers:IPythonLexer
ipython3 = IPython.lib.lexers:IPython3Lexer
ipythonconsole = IPython.lib.lexers:IPythonConsoleLexer

This is so weird to me how this script is set up. Like check this::

    if 'setuptools' in sys.modules:
        setuptools_extra_args['entry_points'] = {
            'console_scripts':
            # find_entry_points(),
            'pygments.lexers': [
                'ipythonconsole = IPython.lib.lexers:IPythonConsoleLexer',
                'ipython = IPython.lib.lexers:IPythonLexer',
                'ipython3 = IPython.lib.lexers:IPython3Lexer',
            ],
        }

So if this user doesn't have setuptools installed, then they don't get the
pygments lexers installed? Wth?

Here's something worth keeping in mind.

>>> import importlib_metadata
>>> importlib_metadata.entry_points()
...  # +ELLIPSIS
EntryPoint(name='iptest', value='IPython.testing.iptestcontroller:main', group='console_scripts'),
EntryPoint(name='iptest3', value='IPython.testing.iptestcontroller:main', group='console_scripts'),
EntryPoint(name='ipython', value='IPython:start_ipython', group='console_scripts'),
EntryPoint(name='ipython3', value='IPython:start_ipython', group='console_scripts'),

"""
from __future__ import print_function

import os
import sys

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

from distutils.command.sdist import sdist

from distutils.command.install_data import install_data
from distutils.util import change_root, convert_path

from distutils.core import setup
try:
    import importlib_metadata
except ImportError:
    importlib_metadata = None

from setuptools import find_packages

isfile = os.path.isfile
pjoin = os.path.join
repo_root = os.path.dirname(os.path.abspath(__file__))


def execfile(fname, globs, locs=None):
    locs = locs or globs
    with open(fname) as f:
        exec(compile(f.read(), fname, "exec"), globs, locs)


# release.py contains version, authors, license, url, keywords, etc.
execfile(pjoin(repo_root, 'IPython', 'core', 'release.py'), globals())

# ------------------------------------------------------------------------------
# Handle OS specific things
# ------------------------------------------------------------------------------

if os.name in ('nt', 'dos'):
    os_name = 'windows'
else:
    os_name = os.name

# Under Windows, 'sdist' has not been supported.  Now that the docs build with
# Sphinx it might work, but let's not turn it on until someone confirms that it
# actually works.
# if os_name == 'windows' and 'sdist' in sys.argv:
#     print('The sdist command is not available under Windows.  Exiting.')
#     sys.exit(1)

# ------------------------------------------------------------------------------
# Things related to the IPython documentation
# ------------------------------------------------------------------------------

# update the manuals when building a source dist
if len(sys.argv) >= 2 and sys.argv[1] in ('sdist', 'bdist_rpm'):

    # List of things to be updated. Each entry is a triplet of args for
    # target_update()
    to_update = [
        ('docs/man/ipython.1.gz', ['docs/man/ipython.1'],
         'cd docs/man && gzip -9c ipython.1 > ipython.1.gz'),
    ]

    [target_update(*t) for t in to_update]

# ---------------------------------------------------------------------------
# Find all the packages, package data, and data_files
# ---------------------------------------------------------------------------

packages = find_packages()
# package_data = find_package_data()

# data_files = find_data_files()

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
    # cmdclass={'install_data': install_data_ext},
    project_urls={
        'Documentation': 'https://ipython.readthedocs.io/',
        'Funding': 'https://numfocus.org/',
        'Source': 'https://github.com/ipython/ipython',
        'Tracker': 'https://github.com/ipython/ipython/issues',
    })

setup_args['packages'] = packages

# setup_args['package_data'] = package_data
# TODO: use resourcemanager API
setup_args['package_data'] = {
    '': ['*.txt', '*.rst'],
    'IPython.core': ['profile/README*'],
    'IPython.core.tests': ['*.png', '*.jpg', 'daft_extension/*.py'],
    'IPython.lib.tests': ['*.wav'],
    'IPython.testing.plugin': ['*.txt'],
}

# For some commands, use setuptools.  Note that we do NOT list install here!
# If you want a setuptools-enhanced install, just run 'setupegg.py install'
needs_setuptools = {
    'develop',
    'release',
    'bdist_egg',
    'bdist_rpm',
    'bdist',
    'bdist_dumb',
    'bdist_wininst',
    'bdist_wheel',
    'egg_info',
    'easy_install',
    'upload',
    'install_egg_info',
}

if len(needs_setuptools.intersection(sys.argv)) > 0:
    import setuptools

# This dict is used for passing extra arguments that are setuptools
# specific to setup
setuptools_extra_args = {}

# setuptools requirements

extras_require = dict(
    parallel=['ipyparallel'],
    qtconsole=['qtconsole'],
    doc=['Sphinx>=1.3'],
    test=[
        'nose>=0.10.1', 'requests', 'testpath', 'pygments', 'nbformat',
        'ipykernel', 'numpy'
    ],
    terminal=[],
    kernel=['ipykernel'],
    nbformat=['nbformat'],
    notebook=['notebook', 'ipywidgets'],
    nbconvert=['nbconvert'],
)

install_requires = [
    'setuptools>=18.5',
    'jedi>=0.10',
    'decorator',
    'pickleshare',
    'traitlets>=4.2',
    'prompt_toolkit>=2.0.0,<2.1.0',
    'pygments',
    'backcall',
]

# Platform-specific dependencies:
# This is the correct way to specify these,
# but requires pip >= 6. pip < 6 ignores these.

extras_require.update({
    ':python_version == "3.4"': ['typing'],
    ':sys_platform != "win32"': ['pexpect'],
    ':sys_platform == "darwin"': ['appnope'],
    ':sys_platform == "win32"': ['colorama'],
    ':sys_platform == "win32" and python_version < "3.6"':
    ['win_unicode_console>=0.5'],
})
# FIXME: re-specify above platform dependencies for pip < 6
# These would result in non-portable bdists.
if not any(arg.startswith('bdist') for arg in sys.argv):
    if sys.platform == 'darwin':
        install_requires.extend(['appnope'])

    if not sys.platform.startswith('win'):
        install_requires.append('pexpect')

    # workaround pypa/setuptools#147, where setuptools misspells
    # platform_python_implementation as python_implementation
    if 'setuptools' in sys.modules:
        for key in list(extras_require):
            if 'platform_python_implementation' in key:
                new_key = key.replace('platform_python_implementation',
                                      'python_implementation')
                extras_require[new_key] = extras_require.pop(key)

everything = set()
for key, deps in extras_require.items():
    if ':' not in key:
        everything.update(deps)
extras_require['all'] = everything

if 'setuptools' in sys.modules:
    setuptools_extra_args['python_requires'] = '>=3.5'
    setuptools_extra_args['zip_safe'] = False
    setuptools_extra_args['entry_points'] = {
        'console_scripts': [
            'iptest = IPython.testing.iptestcontroller:main',
            'iptest3 = IPython.testing.iptestcontroller:main',
            'ipython = IPython:start_ipython',
            'ipython3 = IPython:start_ipython',
        ],
        # find_entry_points(),
        'pygments.lexers': [
            'ipythonconsole = IPython.lib.lexers:IPythonConsoleLexer',
            'ipython = IPython.lib.lexers:IPythonLexer',
            'ipython3 = IPython.lib.lexers:IPython3Lexer',
        ],
    }
    setup_args['extras_require'] = extras_require
    setup_args['install_requires'] = install_requires

# ---------------------------------------------------------------------------
# Do the actual setup now
# ---------------------------------------------------------------------------

setup_args.update(setuptools_extra_args)

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
        self.set_undefined_options('install', ('root', 'root'),
                                   ('force', 'force'),
                                   ('install_base', 'install_base'),
                                   ('install_platbase', 'install_platbase'),
                                   ('install_purelib', 'install_purelib'),
                                   ('install_headers', 'install_headers'),
                                   ('install_lib', 'install_lib'),
                                   ('install_scripts', 'install_scripts'),
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


def main():
    setup(**setup_args)


if __name__ == '__main__':
    sys.exit(main())
