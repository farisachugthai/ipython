"""Can I just go ahead and git rm this?

It's a silly test and we shouldn't be using _detect_screen_size.

shutil.get_terminal_size.
"""
# -----------------------------------------------------------------------------
#  Copyright (C) 2010-2011 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------
import io

# N.B. For the test suite, page.page is overridden (see
# IPython.testing.globalipapp)
from IPython.core import page


def test_detect_screen_size():
    """Simple smoketest for page._detect_screen_size."""
    try:
        page._detect_screen_size(True, 25)
    except (TypeError, io.UnsupportedOperation):
        # This can happen in the test suite, because stdout may not have a
        # fileno.
        pass
