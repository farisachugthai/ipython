#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Setup script for IPython.

Under Posix environments it works like a typical setup.py script.

And now it does on Windows as well.

.. data:: setup_args

    Create a dict with the basic information
    This dict is eventually passed to setup after additional keys are added.

.. data:: setuptools_extra_args

    This dict is used for passing extra arguments that are setuptools
    specific to setup

"""
# -----------------------------------------------------------------------------
#   Copyright (c) 2008-2011, IPython Development Team.
#   Copyright (c) 2001-2007, Fernando Perez <fernando.perez@colorado.edu>
#   Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
#   Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>

#   Distributed under the terms of the Modified BSD License.
# -----------------------------------------------------------------------------
import os
import runpy
import sys
from distutils.command.install_data import install_data
from distutils.util import change_root, convert_path

from setuptools import find_packages, setup

if False:  # shut the linters up
    from IPython.core.release import (
        name,
        version,
        description,
        long_description,
        author,
        author_email,
        url,
        license,
        platforms,
        keywords,
        classifiers,
    )

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists("MANIFEST"):
    os.remove("MANIFEST")

try:
    import importlib_metadata
except ImportError:
    importlib_metadata = None


def execfile(fname, globs, locs=None):
    """TODO: runpy.run_path()."""
    locs = locs or globs
    with open(fname) as f:
        exec(compile(f.read(), fname, "exec"), globs, locs)


# release.py contains version, authors, license, url, keywords, etc.
repo_root = os.path.dirname(os.path.abspath(__file__))
# execfile(os.path.join(repo_root, "IPython", "core", "release.py"), globals())
compile_file = os.path.join(repo_root, "IPython", "core", "release.py")
ns = runpy.run_path(compile_file, init_globals=globals())
if getattr(ns, "version_info", None):
    _version_major, _version_minor, _version_patch, _version_extra = getattr(
        ns, "version_info"
    )
name = ns["name"]
version = ns["version"]
# ------------------------------------------------------------------------------
# Things related to the IPython documentation
# ------------------------------------------------------------------------------

# update the manuals when building a source dist
# if len(sys.argv) >= 2 and sys.argv[1] in ('sdist', 'bdist_rpm'):

# List of things to be updated. Each entry is a triplet of args for
# target_update()
# to_update = [
#     ('docs/man/ipython.1.gz', ['docs/man/ipython.1'],
#      'cd docs/man && gzip -9c ipython.1 > ipython.1.gz'),
# ]

# [target_update(*t) for t in to_update]

# ---------------------------------------------------------------------------
# Find all the packages, package data, and data_files
# ---------------------------------------------------------------------------

# package_data = find_package_data()

# data_files = find_data_files()

setup_args = dict(
    name=ns["name"],
    version=ns["version"],
    description=ns["description"],
    long_description=ns["long_description"],
    author=ns["author"],
    author_email=ns["author_email"],
    url=ns["url"],
    license=ns["license"],
    platforms=ns["platforms"],
    keywords=ns["keywords"],
    classifiers=ns["classifiers"],
    # cmdclass={'install_data': install_data_ext},
    project_urls={
        "Documentation": "https://ipython.readthedocs.io/",
        "Funding": "https://numfocus.org/",
        "Source": "https://github.com/ipython/ipython",
        "Tracker": "https://github.com/ipython/ipython/issues",
    },
)

setup_args["packages"] = find_packages()

# TODO: use resourcemanager API
setup_args["package_data"] = {
    "": ["*.txt", "*.rst"],
    "IPython.core": ["profile/README*"],
    "IPython.core.tests": ["*.png", "*.jpg", "daft_extension/*.py"],
    "IPython.lib.tests": ["*.wav"],
    "IPython.testing.plugin": ["*.txt"],
}

needs_setuptools = {
    "develop",
    "release",
    "bdist_egg",
    "bdist_rpm",
    "bdist",
    "bdist_dumb",
    "bdist_wininst",
    "bdist_wheel",
    "egg_info",
    "easy_install",
    "upload",
    "install_egg_info",
    # cool new pep517 toys
    "build_wheel",
    "build_sdist",
}

setuptools_extra_args = {}

extras_require = dict(
    parallel=["ipyparallel"],
    qtconsole=["qtconsole"],
    # Note: matplotlib is a hard dependency to build the docs
    doc=["Sphinx>=1.3", "matplotlib"],
    # coverage shows up the iptestcontroller and there's no try/excepts
    test=[
        "coverage",
        "ipykernel",
        "matplotlib",
        "matplotlib",
        "nbformat",
        "nose>=0.10.1",
        # how do you make this conditional on OS again?
        # "pexpect",
        "pytest",
        "requests",
        "sphinx",
        "testpath",
    ],
    terminal=[],
    kernel=["ipykernel"],
    nbformat=["nbformat"],
    notebook=["notebook", "ipywidgets"],
    nbconvert=["nbconvert"],
)

install_requires = [
    "setuptools>=38.5",
    "jedi>=0.10",
    "decorator",
    "pickleshare",
    "traitlets>=4.2",
    "prompt_toolkit>=2.0.0,<3.1.0,!=3.0.0,!=3.0.1",
    "pygments",
    "backcall",
]

# Platform-specific dependencies:
extras_require.update(
    {
        ':sys_platform != "win32"': ["pexpect"],
        ':sys_platform == "darwin"': ["appnope"],
        ':sys_platform == "win32"': ["colorama"],
    }
)

if not any(arg.startswith("bdist") for arg in sys.argv):
    if sys.platform == "darwin":
        install_requires.extend(["appnope"])

    if not sys.platform.startswith("win"):
        install_requires.append("pexpect")

    # workaround pypa/setuptools#147, where setuptools misspells
    # platform_python_implementation as python_implementation
    if "setuptools" in sys.modules:
        for key in list(extras_require):
            if "platform_python_implementation" in key:
                new_key = key.replace(
                    "platform_python_implementation", "python_implementation"
                )
                extras_require[new_key] = extras_require.pop(key)

everything = []
for key, deps in extras_require.items():
    if ":" not in key:
        everything.append(deps)

extras_require["all"] = everything

if "setuptools" in sys.modules:
    setuptools_extra_args["python_requires"] = ">=3.6"
    setuptools_extra_args["zip_safe"] = False
    setuptools_extra_args["entry_points"] = {
        "console_scripts": [
            "iptest = IPython.testing.iptestcontroller:main",
            "iptest3 = IPython.testing.iptestcontroller:main",
            "ipython = IPython:start_ipython",
            "ipython3 = IPython:start_ipython",
        ],
        # find_entry_points(),
        "pygments.lexers": [
            "ipythonconsole = IPython.lib.lexers:IPythonConsoleLexer",
            "ipy = IPython.lib.lexers:IPyLexer",
            "ipython3 = IPython.lib.lexers:IPython3Lexer",
            "ipython = IPython.lib.lexers:IPythonLexer",
            "ipytraceback = IPython.lib.lexers:IPythonTracebackLexer",
        ],
    }
    setup_args["extras_require"] = extras_require
    setup_args["install_requires"] = install_requires

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
        self.set_undefined_options(
            "install",
            ("root", "root"),
            ("force", "force"),
            ("install_base", "install_base"),
            ("install_platbase", "install_platbase"),
            ("install_purelib", "install_purelib"),
            ("install_headers", "install_headers"),
            ("install_lib", "install_lib"),
            ("install_scripts", "install_scripts"),
            ("install_data", "install_data"),
        )

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
                base = getattr(self, "install_" + lof[0])
            else:
                base = getattr(self, "install_base")
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
                    # print "DEBUG: ", out  # dbg
                    self.outfiles.append(out)

        return self.outfiles


def main():
    setup(**setup_args)


if __name__ == "__main__":
    sys.exit(main())
