# -*- coding: utf-8 -*-
"""Tests for CommandChainDispatcher."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import nose.tools as nt
from IPython.core.error import TryNext
from IPython.core.hooks import CommandChainDispatcher

# -----------------------------------------------------------------------------
# Local utilities
# -----------------------------------------------------------------------------

# Define two classes, one which succeeds and one which raises TryNext. Each
# sets the attribute `called` to True when it is called.


class Okay(object):
    """

    """

    def __init__(self, message):
        self.message = message
        self.called = False

    def __call__(self):
        self.called = True
        return self.message


class Fail(object):
    """

    """

    def __init__(self, message):
        self.message = message
        self.called = False

    def __call__(self):
        self.called = True
        raise TryNext(self.message)


# -----------------------------------------------------------------------------
# Test functions
# -----------------------------------------------------------------------------


def test_command_chain_dispatcher_ff():
    """Test two failing hooks"""
    fail1 = Fail("fail1")
    fail2 = Fail("fail2")
    dp = CommandChainDispatcher([(0, fail1), (10, fail2)])

    try:
        dp()
    except TryNext as e:
        nt.assert_equal(str(e), "fail2")
    else:
        assert False, "Expected exception was not raised."

    nt.assert_true(fail1.called)
    nt.assert_true(fail2.called)


def test_command_chain_dispatcher_fofo():
    """Test a mixture of failing and succeeding hooks."""
    fail1 = Fail("fail1")
    fail2 = Fail("fail2")
    okay1 = Okay("okay1")
    okay2 = Okay("okay2")

    dp = CommandChainDispatcher(
        [
            (0, fail1),
            # (5, okay1), # add this later
            (10, fail2),
            (15, okay2),
        ]
    )
    dp.add(okay1, 5)

    nt.assert_equal(dp(), "okay1")

    nt.assert_true(fail1.called)
    nt.assert_true(okay1.called)
    nt.assert_false(fail2.called)
    nt.assert_false(okay2.called)


def test_command_chain_dispatcher_eq_priority():
    okay1 = Okay("okay1")
    okay2 = Okay("okay2")
    dp = CommandChainDispatcher([(1, okay1)])
    dp.add(okay2, 1)
