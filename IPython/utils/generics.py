# encoding: utf-8
"""Generic functions for extending IPython.
"""

from IPython.core.error import TryNext
from functools import singledispatch


@singledispatch
def complete_object(obj, prev_completions):
    """Custom completer dispatching for python objects.

    Parameters
    ----------
    obj : object
        The object to complete.
    prev_completions : list
        List of attributes discovered so far.

    This should return the list of attributes in obj. If you only wish to
    add to the attributes already discovered normally, return
    own_attrs + prev_completions.

    Wow. This is imported at core.tests.test_completer *sigh*
    """
    raise TryNext
