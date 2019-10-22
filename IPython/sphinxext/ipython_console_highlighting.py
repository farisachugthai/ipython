#!/usr/bin/env python3
"""reST directive for syntax-highlighting IPython interactive sessions."""
from sphinx import highlighting
import IPython
from IPython.lib import lexers

IPyLexer = lexers.IPyLexer


def setup(app):
    """Setup as a sphinx extension.

    .. seealso:: The official Sphinx documentation

        https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_lexer

    """
    metadata = {'parallel_read_safe': True, 'parallel_write_safe': True}
    return metadata

# Register the extension as a valid pygments lexer.
# Alternatively, we could register the lexer with pygments instead. This would
# require using setuptools entrypoints: http://pygments.org/docs/plugins


ipy2 = IPyLexer(python3=False)
ipy3 = IPyLexer(python3=True)

highlighting.lexers['ipython'] = ipy2
highlighting.lexers['ipython2'] = ipy2
highlighting.lexers['ipython3'] = ipy3
