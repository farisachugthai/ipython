.. _sphinxext-index:

=================
Sphinx extensions
=================

Simply wanted to drop this command as the explanation for why all the
autogen scripts are getting deleted.::

   sphinx-apidoc -o source/api/generated/ -fe --tocfile index ../IPython

Isn't that easier?

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   ipython_sphinx_directive
   lexer
   developers_notes


.. todo:: Need to add rst docs for

   custom_doctests
   configtraits
   magics
   make
