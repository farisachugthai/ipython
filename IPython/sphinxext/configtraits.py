"""Directives and roles for documenting traitlets config options.

::

    .. configtrait:: Application.log_datefmt

        Description goes here.

    Cross reference like this: :configtrait:`Application.log_datefmt`.

"""
# from sphinx.locale import l_
# from sphinx.util.docfields import Field
from typing import Dict, Any, AnyStr

from sphinx.application import Sphinx

from IPython import version_info


def setup(app: "Sphinx") -> Dict[str, Any]:

    app.add_object_type('configtrait', 'configtrait', objname='Config option')
    metadata = {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
        'version': version_info,
    }
    return metadata
