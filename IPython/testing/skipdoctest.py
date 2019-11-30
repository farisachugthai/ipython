"""Decorators marks that a doctest should be skipped.

The :mod:`IPython.testing.decorators` module triggers various extra imports,
including :mod:`numpy` and sympy if they're present.

Since this decorator is used in core parts of IPython,
it's in a separate module so that running IPython doesn't trigger those imports.

.. decorator:: skip_doctest

    Mark a function or method for skipping its doctest.

"""

# Copyright (C) IPython Development Team
# Distributed under the terms of the Modified BSD License.


def skip_doctest(f):
    """ This decorator allows you to blacklist a function from doctesting.

    Although it will be omitted from testing, the docstring will be preserved
    for introspection, help, etc.

    Parameters
    ----------
    f : function
        Function to mark

    Returns
    -------
    f : function

    """
    f.skip_doctest = True
    return f
