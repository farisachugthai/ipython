"""Test help output of various IPython entry points.

Wait what the hell is the trust subcommand?
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import IPython.testing.tools as tt


def test_ipython_help():
    tt.help_all_output_test()


def test_profile_help():
    tt.help_all_output_test("profile")


def test_profile_list_help():
    tt.help_all_output_test("profile list")


def test_profile_create_help():
    tt.help_all_output_test("profile create")


def test_locate_help():
    """12/03/2019: All pass but this one. Unsure what the error message is even saying."""
    tt.help_all_output_test("locate")


def test_locate_profile_help():
    tt.help_all_output_test("locate profile")


# def test_trust_help():
#     tt.help_all_output_test("trust")
