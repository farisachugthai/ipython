# encoding: utf-8
"""IO capturing utilities.

Examples
--------
If you have a CapturedIO object ``c``, these can be displayed in IPython
using::

    from IPython.display import display
    for o in c.outputs:
        display(o)

"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from io import StringIO

# -----------------------------------------------------------------------------
# Classes and functions
# -----------------------------------------------------------------------------


class RichOutput:
    """Seems to be a convenience object to work with IPython display."""

    def __init__(self, data=None, metadata=None, transient=None, update=False):
        """Initialize with the required data.

        Parameters
        ----------
        data :
        metadata :
        transient :
        update :

        """
        self.data = data or {}
        self.metadata = metadata or {}
        self.transient = transient or {}
        self.update = update

    def display(self):
        """
        Imports :func:`IPython.display.publish_display_data` and feeds
        instance attributes to it.
        """
        from IPython.display import publish_display_data

        publish_display_data(
            data=self.data,
            metadata=self.metadata,
            transient=self.transient,
            update=self.update,
        )

    def _repr_mime_(self, mime):
        """I feel like you could make a factory function out of this.

        This is the method that all those other _repr_* methods are calling.
        If we had a list of accepted MIMEtypes, then we could just call them
        based on the list. Idk how to implement that though.

        Parameters
        ----------
        mime :

        Returns
        -------

        """
        if mime not in self.data:
            return
        data = self.data[mime]
        if mime in self.metadata:
            return data, self.metadata[mime]
        else:
            return data

    def _repr_mimebundle_(self, include=None, exclude=None):
        return self.data, self.metadata

    def _repr_html_(self):
        return self._repr_mime_("text/html")

    def _repr_latex_(self):
        return self._repr_mime_("text/latex")

    def _repr_json_(self):
        return self._repr_mime_("application/json")

    def _repr_javascript_(self):
        return self._repr_mime_("application/javascript")

    def _repr_png_(self):
        return self._repr_mime_("image/png")

    def _repr_jpeg_(self):
        return self._repr_mime_("image/jpeg")

    def _repr_svg_(self):
        return self._repr_mime_("image/svg+xml")


class CapturedIO:
    """Simple object for containing captured IO streams.

    This specifically manifests as purely unbuffered writes to
    :data:`sys.stdout`, :data:`sys.stderr` as well as automatic
    creation of rich display StringIO objects.

    Each instance `c` has three attributes:

    Attributes
    ----------
    - 'c.stdout' : str
        Standard output as a string
    - 'c.stderr' : str
        Standard error as a string
    - 'c.outputs' : list
        Rich display outputs

    Methods
    -------
    Additionally, there's a ``c.show()`` method which will print all of the
    above in the same order, and can be invoked simply via ``c()``.

    """

    def __init__(self, stdout, stderr, outputs=None):
        self._stdout = stdout
        self._stderr = stderr
        self._outputs = outputs or []

    def __str__(self):
        return self.stdout

    @property
    def stdout(self):
        """Captured :data:`sys.stdout`."""
        if not self._stdout:
            return ""
        return self._stdout.getvalue()

    @property
    def stderr(self):
        """Captured :data:`sys.stderr`."""
        if not self._stderr:
            return ""
        return self._stderr.getvalue()

    @property
    def outputs(self):
        """A list of the captured rich display outputs, if any.

        If you have a CapturedIO object ``c``, these can be displayed in IPython
        using::

            from IPython.display import display
            for o in c.outputs:
                display(o)

        """
        return [RichOutput(**kargs) for kargs in self._outputs]

    def show(self):
        """write my output to sys.stdout/err as appropriate"""
        sys.stdout.write(self.stdout)
        sys.stderr.write(self.stderr)
        sys.stdout.flush()
        sys.stderr.flush()
        for kargs in self._outputs:
            RichOutput(**kargs).display()

    __call__ = show


class capture_output:
    """Context manager for capturing stdout/err.

    .. tip::
        Probably one of the more heavily used classes in the test
        suite. Tread lightly if you modify!

    .. todo:: Should this subclass :class:`contextlib.abstractcontextmanager`?

    Note
    ----
    The existence of :func:`contextlib.redirect_stdout` and
    :func:`contextlib.redirect_stderr`.

    """

    stdout = True
    stderr = True
    display = True

    def __init__(self, stdout=True, stderr=True, display=True):
        self.stdout = stdout
        self.stderr = stderr
        self.display = display
        self.shell = None

    def __enter__(self):
        from IPython.core.getipython import get_ipython
        from IPython.core.displaypub import CapturingDisplayPublisher
        from IPython.core.displayhook import CapturingDisplayHook

        self.sys_stdout = sys.stdout
        self.sys_stderr = sys.stderr

        if self.display:
            self.shell = get_ipython()
            if self.shell is None:
                self.save_display_pub = None
                self.display = False

        stdout = stderr = outputs = None
        if self.stdout:
            stdout = sys.stdout = StringIO()
        if self.stderr:
            stderr = sys.stderr = StringIO()
        if self.display:
            self.save_display_pub = self.shell.display_pub
            self.shell.display_pub = CapturingDisplayPublisher()
            outputs = self.shell.display_pub.outputs
            self.save_display_hook = sys.displayhook
            sys.displayhook = CapturingDisplayHook(shell=self.shell, outputs=outputs)

        return CapturedIO(stdout, stderr, outputs)

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.sys_stdout
        sys.stderr = self.sys_stderr
        if self.display and self.shell:
            self.shell.display_pub = self.save_display_pub
            sys.displayhook = self.save_display_hook
