"""Set up IPython for pytest.

.. versionchanged:: v7.11.0.dev

    Stop calling inject directly.

"""

import pytest

# adding this here not because we need them yet but they're good reminders.
# from _pytest.nose import (
#     pytest_runtest_setup,
#     teardown_nose,
#     is_potential_nosetest,
#     call_optional,
# )

# noqa

import IPython


def get_test_shell():
    """Changed the name from canonical get_ipython.

    If we need to call that function direclty, import it and do so.
    """
    # This will get replaced by the real thing once we start IPython below
    return start_test_shell()


@pytest.fixture(scope="session", autouse=True)
def ip():
    return get_test_shell()


@pytest.fixture(scope="session", autouse=True)
def _ip():
    """I'm gonna try and catch both of the typical calls to the shell with this."""
    return get_test_shell()


def start_test_shell():
    """Starts an instance of our shell. It doesn't modify the state too much though.

    No cheating before the test starts!
    """
    # Create custom argv and namespaces for our IPython to be test-friendly
    config = IPython.testing.tools.default_config()
    config.TerminalInteractiveShell.simple_prompt = True

    # Create and initialize our test-friendly IPython instance.
    shell = IPython.terminal.interactiveshell.TerminalInteractiveShell.instance(
        config=config,
    )

    def nopage(strng, start=0, screen_lines=0, pager_cmd=None):
        """Override paging, so we don't require user interaction during the tests.

        Parameters
        ----------
        strng :
        start :
        screen_lines :
        pager_cmd :
        """
        if isinstance(strng, dict):
            strng = strng.get("text/plain", "")
        print(strng)

    IPython.core.page.pager_page = nopage

    return _ip


# @pytest.fixture(scope='session')
# def work_path():
#     path = pathlib.Path("./tmp-ipython-pytest-profiledir")
#     os.environ["IPYTHONDIR"] = str(path.absolute())
#     if path.exists():
#         raise ValueError(
#             'IPython dir temporary path already exists ! Did previous test run exit successfully ?')
#     path.mkdir()
#     yield
#     shutil.rmtree(str(path.resolve()))


@pytest.fixture(autouse=True, scope="session")
def inject():
    """
    for things to work correctly we would need this as a session fixture;
    unfortunately this will fail on some test that get executed as _collection_
    time (before the fixture run), in particular parametrized test that contain
    yields. so for now execute at import time.

    """
