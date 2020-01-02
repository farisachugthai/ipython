import builtins
import os
import pathlib
import shutil
import sys
import tempfile
import types

import pytest

import IPython
from IPython.testing.tools import default_config
from IPython.terminal.interactiveshell import TerminalInteractiveShell

from IPython.testing import tools


# So we can ensure we don't have permission errors running the tests
if os.environ.get("TMP", None):
    tempfile.tempdir = os.environ.get("TMP")
elif os.environ.get("TEMP", None):
    tempfile.tempdir = os.environ.get("TEMP")
elif os.environ.get("TMPDIR", None):
    tempfile.tempdir = os.environ.get("TMPDIR")
elif os.environ.get("XDG_CACHE_HOME", None):
    tempfile.tempdir = os.environ.get("XDG_CACHE_HOME")




def get_ipython():
    if TerminalInteractiveShell._instance:
        return TerminalInteractiveShell.instance()

    config = tools.default_config()
    config.TerminalInteractiveShell.simple_prompt = True

    config.TerminalInteractiveShell.profile_dir = tempfile.mkdtemp()
    config.InteractiveShellApp.exec_files=[]

    # Create and initialize our test-friendly IPython instance.
    shell = TerminalInteractiveShell.instance(config=config)
    return shell


# @pytest.fixture(scope='session', autouse=True)
def work_path():
    path = pathlib.Path("./tmp-ipython-pytest-profiledir")
    os.environ["IPYTHONDIR"] = str(path.absolute())
    if path.exists():
        raise ValueError('IPython dir temporary path already exists ! Did previous test run exit successfully ?')
    path.mkdir()
    yield
    shutil.rmtree(str(path.resolve()))


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

def nopage(strng, start=0, screen_lines=0, pager_cmd=None):
    if isinstance(strng, dict):
        strng = strng.get("text/plain", "")
    print(strng)


def xsys(self, cmd):
    """Replace the default system call with a capturing one for doctest.
    """
    # We use getoutput, but we need to strip it because pexpect captures
    # the trailing newline differently from commands.getoutput
    print(self.getoutput(cmd, split=False, depth=1).rstrip(), end="", file=sys.stdout)
    sys.stdout.flush()


# for things to work correctly we would need this as a session fixture;
# unfortunately this will fail on some test that get executed as _collection_
# time (before the fixture run), in particular parametrized test that contain
# yields. so for now execute at import time.
#@pytest.fixture(autouse=True, scope='session')
def inject():

    builtins.get_ipython = get_ipython
    builtins._ip = get_ipython()
    builtins.ip = get_ipython()
    builtins.ip.system = types.MethodType(xsys, ip)
    builtins.ip.builtin_trap.activate()
    from .core import page

    page.pager_page = nopage
    # yield

inject()
