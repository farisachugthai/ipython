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
   doctest_handlers
   lexer
   developers_notes


.. todo:: Need to add rst docs for

   custom_doctests
   configtraits
   magics

Actually that might not prove too urgent.

See Also
--------
:mod:`IPython.sphinxext.custom_doctests`
:mod:`IPython.sphinxext.configtraits`
:mod:`IPython.sphinxext.magics`

