"""Test installing editor hooks"""
import sys
from unittest import mock

import nose.tools as nt

from IPython.core.getipython import get_ipython
from IPython.lib.editorhooks import install_editor


def test_install_editor():
    called = []

    def fake_popen(*args, **kwargs):
        """

        Parameters
        ----------
        args :
        kwargs :

        Returns
        -------

        """
        called.append(
            {"args": args, "kwargs": kwargs, }
        )
        return mock.MagicMock(**{"wait.return_value": 0})

    install_editor("foo -l {line} -f {filename}", wait=False)

    with mock.patch("subprocess.Popen", fake_popen):
        get_ipython().hooks.editor("the file", 64)

    # Is this supposed to be in the with statement?
    nt.assert_equal(len(called), 1)
    args = called[0]["args"]
    kwargs = called[0]["kwargs"]

    nt.assert_equal(kwargs, {"shell": True})

    if sys.platform.startswith("win"):
        expected = ["foo", "-l", "64", "-f", "the file"]
    else:
        expected = "foo -l 64 -f 'the file'"
    cmd = args[0]
    nt.assert_equal(cmd, expected)
