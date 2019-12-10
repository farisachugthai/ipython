"""Tried moving 1 function over and look at the hoops you gotta jump through."""
import sys
from tempfile import TemporaryDirectory

if sys.version_info < (3, 7):
    from IPython.core.error import ModuleNotFoundError

try:
    import docrepr
except (ImportError, ModuleNotFoundError):
    pass


def sphinxified(doc):
    """

    Parameters
    ----------
    doc :

    Returns
    -------
    mimebundle
    """
    with TemporaryDirectory() as dirname:
        return {
            "text/html": docrepr.sphinxify.sphinxify(doc, dirname),
            "text/plain": doc,
        }
