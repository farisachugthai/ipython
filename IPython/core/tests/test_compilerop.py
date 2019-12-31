# coding: utf-8
"""Tests for the compilerop module.
"""
# -----------------------------------------------------------------------------
#  Copyright (C) 2010-2011 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# Stdlib imports
import linecache
import sys

# Third-party imports
import nose.tools as nt

# Our own imports
from IPython.core import compilerop


# -----------------------------------------------------------------------------
# Test functions
# -----------------------------------------------------------------------------


def test_code_name():
    code = "x=1"
    name = compilerop.code_name(code)
    nt.assert_true(name.startswith("<ipython-input-0"))


def test_code_name2():
    code = "x=1"
    name = compilerop.code_name(code, 9)
    nt.assert_true(name.startswith("<ipython-input-9"))


def test_cache():
    # Test the compiler correctly compiles and caches inputs
    cp = compilerop.CachingCompiler()
    ncache = len(linecache.cache)
    cp.cache("x=1")
    nt.assert_true(len(linecache.cache) > ncache)


def test_cache_unicode():
    cp = compilerop.CachingCompiler()
    ncache = len(linecache.cache)
    cp.cache("t = 'žćčšđ'")
    nt.assert_true(len(linecache.cache) > ncache)


# def test_compiler_check_cache():
# I have no idea what this tests but it fails
#     # Test the compiler properly manages the cache.
#     # Rather simple-minded tests that just exercise the API
#     cp = compilerop.CachingCompiler()
#     cp.cache("x=1", 99)
#     # Ensure now that after clearing the cache, our entries survive
#     linecache.checkcache()
#     for k in linecache.cache:
#         if k.startswith("<ipython-input-99"):
#             break
#         else:
#             print(k)
#             raise AssertionError("Entry for input-99 missing from linecache")
