import pytest
from IPython import lib


def todo():
    """This doesn't behave the way I want but I'm unsure how to correctly
    skip a module based on imports. This will skip the whole suite."""
    inputhookglut = pytest.importorskip("glut")
    inputhookgtk3 = pytest.importorskip("gtk3")
    inputhookqt4 = pytest.importorskip("qt4")
    inputhookwx = pytest.importorskip("wx")
