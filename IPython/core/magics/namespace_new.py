import shutil
from IPython.core.getipython import get_ipython
from IPython.core.magic import Magics, magics_class, line_magic

from .packaging import _is_conda_workspace


def conda():
    """Simpler re-implemented line magic."""
    conda = shutil.which("conda")
    if conda.endswith("bat"):
        conda = "call " + conda
    # %sx conda
