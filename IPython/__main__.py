# encoding: utf-8
"""Terminal-based IPython entry point.
"""
# -----------------------------------------------------------------------------
#  Copyright (c) 2012, IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import locale
from IPython import start_ipython

locale.setlocale(locale.LC_ALL, "")
start_ipython()
