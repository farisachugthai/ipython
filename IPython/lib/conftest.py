import pytest
from IPython import lib


inputhookglut = pytest.importorskip('glut')
inputhookgtk3 = pytest.importorskip('gtk3')
inputhookpyglet = pytest.importorskip('pyglet')
inputhookqt4 = pytest.importorskip('qt4')
inputhookwx = pytest.importorskip('wx')
