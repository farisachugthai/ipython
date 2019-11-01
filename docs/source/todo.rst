:orphan:

.. _todo:

====
TODO
====


:date: Oct 27, 2019

These are just my personal observations of things that need to get fixed up.

Remove all references to `IPython.core.inputtransformer` and `IPython.core.inputsplitter` in the tests.

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


Command line options
--------------------

Oct 29, 2019:

Did I do something wrong or does the quick option still execute startup files?

.. sourcecode:: bash

   * $: ipython --quick

   Python 3.7.3 (default, Apr  3 2019, 19:16:38)
   Type 'copyright', 'credits' or 'license' for more information

   IPython 7.10.0.dev -- An enhanced Interactive Python. Type '?' for help.
   [TerminalIPythonApp] WARNING | Unknown error in handling startup files:

The old inputhook doc.

=========================
IPython GUI Support Notes
=========================

IPython allows GUI event loops to be run in an interactive IPython session.
This is done using Python's PyOS_InputHook hook which Python calls
when the :func:`raw_input` function is called and waiting for user input.
IPython has versions of this hook for wx, pyqt4 and pygtk.

When a GUI program is used interactively within IPython, the event loop of
the GUI should *not* be started. This is because, the PyOS_Inputhook itself
is responsible for iterating the GUI event loop.

IPython has facilities for installing the needed input hook for each GUI
toolkit and for creating the needed main GUI application object. Usually,
these main application objects should be created only once and for some
GUI toolkits, special options have to be passed to the application object
to enable it to function properly in IPython.

We need to answer the following questions:

* Who is responsible for creating the main GUI application object, IPython
  or third parties (matplotlib, enthought.traits, etc.)?

* What is the proper way for third party code to detect if a GUI application
  object has already been created?  If one has been created, how should
  the existing instance be retrieved?

* In a GUI application object has been created, how should third party code
  detect if the GUI event loop is running. It is not sufficient to call the
  relevant function methods in the GUI toolkits (like ``IsMainLoopRunning``)
  because those don't know if the GUI event loop is running through the
  input hook.

* We might need a way for third party code to determine if it is running
  in IPython or not.  Currently, the only way of running GUI code in IPython
  is by using the input hook, but eventually, GUI based versions of IPython
  will allow the GUI event loop in the more traditional manner. We will need
  a way for third party code to distinguish between these two cases.

Here is some sample code I have been using to debug this issue::

    from matplotlib import pyplot as plt

    from enthought.traits import api as traits

    class Foo(traits.HasTraits):
        a = traits.Float()

    f = Foo()
    f.configure_traits()

    plt.plot(range(10))

