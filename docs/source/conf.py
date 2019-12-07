# -*- coding: utf-8 -*-
"""
IPython documentation build configuration file.

NOTE: This file has been edited manually from the auto-generated one from
sphinx.  Do NOT delete and re-generate.  If any changes from sphinx are
needed, generate a scratch one and merge by hand any new fields needed.


This file is execfile()d with the current directory set to its containing dir.

The contents of this file are pickled, so don't put values in the namespace
that aren't pickleable (module imports are okay, they're removed automatically).

All configuration values have a default value; values that are commented out
serve to show the default value.
"""
import logging
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Dict, Any

from IPython import sphinxext  # noqa
from IPython.sphinxext import (configtraits, ipython_directive,
                               magics, github)  # noqa F401
from IPython.lib.lexers import IPyLexer, IPythonTracebackLexer
import sphinx
from sphinx.util.docfields import GroupedField
from sphinx.util.logging import getLogger
from sphinx.application import Sphinx

import numpydoc  # noqa F401
try:
    from matplotlib.sphinxext.plot_directive import PlotDirective
except ImportError:
    PlotDirective = None

logger = getLogger(__name__)
logger.setLevel(logging.DEBUG)

root = Path('../..').resolve()
logging.debug('root dir is: {}'.format(root))

ipython_package = root.joinpath('IPython')
sphinxext = ipython_package.joinpath('sphinxext')
if sphinxext.is_dir():
    sys.path.append(sphinxext.__fspath__())

# http://read-the-docs.readthedocs.io/en/latest/faq.html
ON_RTD = os.environ.get('READTHEDOCS', None) == 'True'

if ON_RTD:
    tags.add('rtd')

else:
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# We load the ipython release info into a dict by explicit execution
iprelease = {}
exec(compile(open('../../IPython/core/release.py').read(),
             '../../IPython/core/release.py', 'exec'), iprelease)

# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    # terrible idea don't do it
    # 'sphinx.ext.autosectionlabel',
    'sphinx.ext.doctest',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.napoleon',  # to preprocess docstrings
    'numpydoc.numpydoc',
    # 'autoapi.extension',
    'github',  # for easy GitHub links
    'magics',
    'configtraits',
]

extensions.extend([
    'IPython.sphinxext.ipython_directive',
])

# autoapi_type = 'python'
# autoapi_dirs = ['../../IPython']
# autoapi_generate_api_docs = False

if shutil.which('dot'):
    extensions.append('sphinx.ext.graphviz')

if PlotDirective is not None:
    extensions.append('matplotlib.sphinxext.plot_directive')

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

rst_prolog = ''


def is_stable(extra):
    for ext in {'dev', 'b', 'rc'}:
        if ext in extra:
            return False
    return True


if is_stable(iprelease['_version_extra']):
    tags.add('ipystable')
    logger.info('Adding Tag: ipystable')
else:
    tags.add('ipydev')
    logger.info('Adding Tag: ipydev')
    rst_prolog += """
.. warning::

    This documentation covers a development version of IPython. The development
    version may differ significantly from the latest stable release.
"""

rst_prolog += """
.. important::

    This documentation covers IPython versions 6.0 and higher. Beginning with
    version 6.0, IPython stopped supporting compatibility with Python versions
    lower than 3.3 including all versions of Python 2.7.

    If you are looking for an IPython version compatible with Python 2.7,
    please use the IPython 5.x LTS release and refer to its documentation (LTS
    is the long term support release).

"""

# The master toctree document.
master_doc = 'index'

# General substitutions.
project = 'IPython'
copyright = 'The IPython Development Team'

# ghissue config
github_project_url = "https://github.com/ipython/ipython"

trim_doctest_flags = True

highlight_language = 'ipython'

# warning_is_error = True
warning_is_error = False

# The default replacements for |version| and |release|, also used in various
# other places throughout the built documents.
#
# The full version, including alpha/beta/rc tags.
release = "%s" % iprelease['version']
# Just the X.Y.Z part, no '-dev'
version = iprelease['version'].split('-', 1)[0]

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
unused_docs = ['api/generated/IPython', 'api/generated/IPython.core']

# Exclude these glob-style patterns when looking for source files. They are
# relative to the source/ directory.
exclude_patterns = ['**test**']

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# Set the default role so we can use `foo` instead of ``foo``

default_role = 'py:obj'

# Options for HTML output
# -----------------------

# Use our syntax highlighting by default
highlight_language = 'ipython'

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
# html_style = 'default.css'


# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
# html_title = None

# The name of an image file (within the static path) to place at the top of
# the sidebar.
# html_logo = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Favicon needs the directory name
html_favicon = '_static/favicon.ico'
# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
html_additional_pages = {
    'interactive/htmlnotebook': 'notebook_redirect.html',
    'interactive/notebook': 'notebook_redirect.html',
    'interactive/nbconvert': 'notebook_redirect.html',
    'interactive/public_server': 'notebook_redirect.html',
}

# If false, no module index is generated.
# html_use_modindex = True

# If true, the reST sources are included in the HTML build as _sources/<name>.
# html_copy_source = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'ipythondoc'

# Options for LaTeX output
# ------------------------

# The paper size ('letter' or 'a4').
latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
latex_font_size = '11pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).

# latex_documents = [
#     ('index', 'ipython.tex', 'IPython Documentation',
#      u"""The IPython Development Team""", 'manual', True),
#     ('parallel/winhpc_index', 'winhpc_whitepaper.tex',
#      'Using IPython on Windows HPC Server 2008',
#      u"Brian E. Granger", 'manual', True)
# ]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# Additional stuff for the LaTeX preamble.
# latex_preamble = ''

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
latex_use_modindex = True

# Options for texinfo output
# --------------------------

# texinfo_documents = [
#     (master_doc, 'ipython', 'IPython Documentation',
#      'The IPython Development Team',
#      'IPython',
#      'IPython Documentation',
#      'Programming',
#      1),
# ]

# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
manpages_url = 'https://linux.die.net/man/'

man_show_urls = True

# -- Extension configuration -------------------------------------------------

# -- Numpydoc ----------------------------------------------

# numpydoc config
# Otherwise Sphinx emits thousands of warnings
numpydoc_show_class_members = False
numpydoc_class_members_toctree = False

# -- Options for intersphinx extension ---------------------------------------

intersphinx_mapping = {'python': ('https://docs.python.org/3/', None),
                       'rpy2': ('https://rpy2.readthedocs.io/en/version_2.8.x/', None),
                       'jupyterclient': ('https://jupyter-client.readthedocs.io/en/latest/', None),
                       'ipyparallel': ('https://ipyparallel.readthedocs.io/en/latest/', None),
                       'jupyter': ('https://jupyter.readthedocs.io/en/latest/', None),
                       'jedi': ('https://jedi.readthedocs.io/en/latest/', None),
                       'traitlets': ('https://traitlets.readthedocs.io/en/latest/', None),
                       'ipykernel': ('https://ipykernel.readthedocs.io/en/latest/', None),
                       'prompt_toolkit': ('https://python-prompt-toolkit.readthedocs.io/en/stable/', None),
                       'ipywidgets': ('https://ipywidgets.readthedocs.io/en/stable/', None),
                       'pip': ('https://pip.pypa.io/en/stable/', None)
                       }

# -- IPython directive -------------------------------------------------------

ipython_warning_is_error = False

ipython_execlines = [
    'import numpy',
    'import IPython',
    'import matplotlib as mpl',
    'import matplotlib.pyplot',
]

# -------------------------------------------------------------------
# Autosummary
# -------------------------------------------------------------------

# How it appears on the website currently is core.magics.*
# So ignore the ``IPython.`` prefix
modindex_common_prefix = ['IPython.']

if sphinx.version_info < (1, 8):
    autodoc_default_flags = ['members', 'undoc-members']
else:
    autodoc_default_options = {
        'member-order': 'bysource',
        'undoc-members': True,
        'show-inheritance': False,
        # might need to comment the below out
        # 'noindex': True,
    }

apidoc_options = {
    'members': False,
    'undoc-members': True,
    'show-inheritance': False,
}

autodoc_inherit_docstrings = False
# autosummary_generate = True

autosummary_imported_members = False

# autoclass_content = u'both'
# autodoc_member_order = u'bysource'
autodoc_member_order = u'groupwise'

autodoc_docstring_signature = True

# Cleanup
# -------
# delete release info to avoid pickling errors from sphinx

del iprelease


# Extension Interface
# -----------------------

from sphinx import addnodes  # noqa

event_sig_re = re.compile(r'([a-zA-Z-]+)\s*\((.*)\)')


def parse_event(env, sig, signode):
    m = event_sig_re.match(sig)
    if not m:
        signode += addnodes.desc_name(sig, sig)
        return sig
    name, args = m.groups()
    signode += addnodes.desc_name(name, name)
    plist = addnodes.desc_parameterlist()
    for arg in args.split(','):
        arg = arg.strip()
        plist += addnodes.desc_parameter(arg, arg)
    signode += plist
    return name


def setup(app: "Sphinx") -> None:
    """Add in the Sphinx directive for `confval`.

    Also define the IPyLexer's while we're here.

    12/03/19: Gonna add trait as a role.
    """
    app.add_object_type('confval', 'confval',
                        objname='configuration value',
                        indextemplate='pair: %s; configuration value')

    app.add_lexer('ipythontb', IPythonTracebackLexer)
    app.add_lexer('ipython', IPyLexer)

    fdesc = GroupedField('param', label='Parameters',
                         names=['param'], can_collapse=True)
    app.add_object_type('directive', 'dir', 'pair: %s; directive')
    app.add_object_type('event', 'event', 'pair: %s; event', parse_event,
                        doc_field_types=[fdesc])

    # workaround for RTD
    app.info = lambda *args, **kwargs: logger.info(*args, **kwargs)
    app.warn = lambda *args, **kwargs: logger.warning(*args, **kwargs)
    app.debug = lambda *args, **kwargs: logger.debug(*args, **kwargs)
