"""Tests for platutils.py,"""

# -----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shutil import which as find_cmd
from subprocess import CalledProcessError as FindCmdError
import sys
import os
from os import system

import nose.tools as nt

from IPython.utils.process import arg_split
from IPython.utils._process_common import (
    getoutput,
    getoutputerror,
    get_output_error_code,
)

from IPython.testing import decorators as dec
from IPython.testing.decorators import has_pywin32
from IPython.testing import tools as tt

py_basename = os.path.basename(sys.executable)

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


# @dec.skip_win32
# believe it or not git for windows has ls. check it regardless
def test_find_cmd_ls():
    """Make sure we can find the full path to ls."""
    path = find_cmd("ls")
    if path is not None:
        nt.assert_true(path.endswith("ls"))


@dec.onlyif(has_pywin32, "This test requires win32api to run")
def test_find_cmd_pythonw():
    """Try to find pythonw on Windows."""
    path = find_cmd("pythonw")
    assert path.lower().endswith("pythonw.exe"), path


@dec.skip_win32
def test_arg_split():
    """Ensure that argument lines are correctly split like in a shell."""
    tests = [
        ["hi", ["hi"]],
        [u"hi", [u"hi"]],
        ["hello there", ["hello", "there"]],
        # \u01ce == \N{LATIN SMALL LETTER A WITH CARON}
        # Do not use \N because the tests crash with syntax error in
        # some cases, for example windows python2.6.
        [u"h\u01cello", [u"h\u01cello"]],
        ['something "with quotes"', ["something", '"with quotes"']],
    ]
    for argstr, argv in tests:
        nt.assert_equal(arg_split(argstr), argv)


@dec.skip_if_not_win32
def test_arg_split_win32():
    """Ensure that argument lines are correctly split like in a shell."""
    tests = [
        ["hi", ["hi"]],
        [u"hi", [u"hi"]],
        ["hello there", ["hello", "there"]],
        [u"h\u01cello", [u"h\u01cello"]],
        ['something "with quotes"', ["something", "with quotes"]],
    ]
    for argstr, argv in tests:
        nt.assert_equal(arg_split(argstr), argv)


class SubProcessTestCase(tt.TempFileMixin):
    def setUp(self):
        """Make a valid python temp file."""
        lines = [
            "import sys",
            "print('on stdout', end='', file=sys.stdout)",
            "print('on stderr', end='', file=sys.stderr)",
            "sys.stdout.flush()",
            "sys.stderr.flush()",
        ]
        self.mktmp("\n".join(lines))

    def test_system(self):
        status = system('%s "%s"' % (py_basename, self.fname))
        self.assertEqual(status, 0)

    def test_system_quotes(self):
        status = system('%s -c "import sys"' % py_basename)
        self.assertEqual(status, 0)

    def test_getoutput(self):
        out = getoutput('%s "%s"' % (py_basename, self.fname))
        # we can't rely on the order the line buffered streams are flushed
        try:
            self.assertEqual(out, b"on stderron stdout")
        except AssertionError:
            self.assertEqual(out, b"on stdouton stderr")

    def test_getoutput_quoted(self):
        out = getoutput('%s -c "print (1)"' % py_basename)
        self.assertEqual(out.strip(), "1")

    # Invalid quoting on windows
    @dec.skip_win32
    def test_getoutput_quoted2(self):
        out = getoutput("%s -c 'print (1)'" % py_basename)
        self.assertEqual(out.strip(), "1")
        out = getoutput("%s -c 'print (\"1\")'" % py_basename)
        self.assertEqual(out.strip(), "1")

    def test_getoutput_error(self):
        out, err = getoutputerror('%s "%s"' % (py_basename, self.fname))
        self.assertEqual(out, b"on stdout")
        self.assertEqual(err, b"on stderr")

    def test_get_output_error_code(self):
        quiet_exit = '%s -c "import sys; sys.exit(1)"' % py_basename
        out, err, code = get_output_error_code(quiet_exit)
        self.assertEqual(out, b"")
        self.assertEqual(err, b"")
        self.assertEqual(code, 1)
        out, err, code = get_output_error_code('%s "%s"' % (py_basename, self.fname))
        self.assertEqual(out, b"on stdout")
        self.assertEqual(err, b"on stderr")
        self.assertEqual(code, 0)
