.. _todo:

====
TODO
====

:date: Oct 27, 2019

These are just my personal observations of things that need to get fixed up.

Remove all references to IPython.core.inputtransformer and IPython.core.inputsplitter in the tests.

It was successfully removed from the code base but hasn't been from
the tests.

Flatten the docs they're really hard to navigate.

The get_ipython().db attribute is seemingly completely undocumented.

I just happened to stumble upon it while rummaging through the tests but why.

Continue working on the sphinxext docs and also consider rewriting our directive.

Docs still don't build.

YES THEY DO! Got them working again and now it's a lot cleaner and emits way less warnings.

Nosetests works.
Pytest will collect ~500 modules and crash.
