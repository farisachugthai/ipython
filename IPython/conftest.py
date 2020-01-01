"""Set up IPython for pytest.

.. versionchanged:: v7.11.0.dev

    Stop calling inject directly.

"""
import os.path
import os
import tempfile
from pathlib import Path

import pytest

import IPython
from IPython.testing.tools import default_config
from IPython.terminal.interactiveshell import TerminalInteractiveShell

# adding this here not because we need them yet but they're good reminders.
from _pytest.nose import (
    #     pytest_runtest_setup,
    #     teardown_nose,
    is_potential_nosetest,
    #     call_optional,
)


# So we can ensure we don't have permission errors running the tests
if os.environ.get("TMP", None):
    tempfile.tempdir = os.environ.get("TMP")
elif os.environ.get("TEMP", None):
    tempfile.tempdir = os.environ.get("TEMP")
elif os.environ.get("TMPDIR", None):
    tempfile.tempdir = os.environ.get("TMPDIR")
elif os.environ.get("XDG_CACHE_HOME", None):
    tempfile.tempdir = os.environ.get("XDG_CACHE_HOME")


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
    config = default_config()
    config.TerminalInteractiveShell.simple_prompt = True

    # Create and initialize our test-friendly IPython instance.
    shell = TerminalInteractiveShell.instance(config=config,)

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


@pytest.fixture(scope='session')
def work_path():
    path = pathlib.Path("./tmp-ipython-pytest-profiledir")
    os.environ["TEST_IPYTHONDIR"] = str(path.absolute())
    if path.exists():
        raise ValueError(
            'IPython dir temporary path already exists ! Did previous test run exit successfully ?')
    path.mkdir()
    yield
    shutil.rmtree(str(path.resolve()))


# Here is a conftest.py file adding a --runslow command line option to control skipping of pytest.mark.slow marked tests:

# content of conftest.py
def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # If you want to postprocess test reports and need access to the executing
    #  environment you can implement a hook that gets called when the test
    # “report” object is about to be created. Here we write out all failing test # calls and also access a fixture(if it was used by the test) in case you
    # want to query / look at it during your post processing. In our case we
    # just write some information out to a failures file:

    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # we only look at actual failing test calls, not setup/teardown
    if rep.when == "call" and rep.failed:
        mode = "a" if os.path.exists("failures") else "w"
        with open("failures", mode) as f:
            # let's also access a fixture for the fun of it
            if "tmpdir" in item.fixturenames:
                extra = " ({})".format(item.funcargs["tmpdir"])
            else:
                extra = ""

            f.write(rep.nodeid + extra + "\n")
