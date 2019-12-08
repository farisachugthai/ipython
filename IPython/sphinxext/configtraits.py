"""Directives and roles for documenting traitlets config options.

::

    .. configtrait:: Application.log_datefmt

        Description goes here.

    Cross reference like this: :configtrait:`Application.log_datefmt`.

"""
# from sphinx.locale import l_
# from sphinx.util.docfields import Field
from typing import Dict, Any

from sphinx.application import Sphinx

from IPython.core.release import version_info


def setup(app: "Sphinx") -> Dict[str, Any]:
    """12/03/19: Added `trait` as a role.

    Exception occured:
    ...
    AttributeError: 'str' object has no attribute 'options'
    # app.add_role('trait', 'configtrait')
    So we can't do this.

    Extension error: The configtrait role is already registered.
    app.add_object_type('trait', 'configtrait', objname='Config option')

    We can't just duplicate the object. Hm.
    """
    app.add_object_type("configtrait", "configtrait", objname="Config option")

    metadata = {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "version": version_info,
    }
    return metadata
