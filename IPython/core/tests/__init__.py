import logging

from IPython.core.getipython import get_ipython

try:
    import nose
except ImportError:
    logging.warn("Nose not installed!")

try:
    from _pytest import unittest
except:
    import unittest


def setup_package():
    """How crazy is it we don't do this? Should modify this so that it uses the globalipapp or whatever though."""
    ip = get_ipython()
    _ip = get_ipython()
