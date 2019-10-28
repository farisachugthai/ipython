#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""From numpy_financial.

:date: Oct 27, 2019

This script was used to generate the rst function stubs
numpy_financial.fv.rst, numpy_financial.ipmt.rst, etc.
It requires that numpy_financial is already installed,
although it could just as easily use a hard-coded list
of function names.
"""
import os

import IPython


def generate_rst_function_files(prefix=None):
    names = [name for name in dir(IPython) if not name.startswith('_')]
    for name in names:
        with open(os.path.join(prefix, name) + '.rst', 'wt') as f:
            f.write('''{name}
{underline}

.. currentmodule:: IPython

.. toctree::

.. autofunction:: {name}
'''.format(name=name, underline='=' * len(name)))


if __name__ == "__main__":
    prefix = os.path.join('source', 'api', 'generated')
    generate_rst_function_files(prefix)
