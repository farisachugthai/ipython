# coding: utf-8
"""

"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.core.getipython import get_ipython

# -----------------------------------------------------------------------------
# wx
# -----------------------------------------------------------------------------


def get_app_wx(*args, **kwargs):
    """Create a new wx app or return an exiting one."""
    import wx

    app = wx.GetApp()
    if app is None:
        if "redirect" not in kwargs:
            kwargs["redirect"] = False
        app = wx.PySimpleApp(*args, **kwargs)
    return app


def is_event_loop_running_wx(app=None):
    """Is the wx event loop running."""
    # New way: check attribute on shell instance
    ip = get_ipython()
    if ip is not None:
        if ip.active_eventloop and ip.active_eventloop == "wx":
            return True
        # Fall through to checking the application, because Wx has a native way
        # to check if the event loop is running, unlike Qt.

    # Old way: check Wx application
    if app is None:
        app = get_app_wx()
    if hasattr(app, "_in_event_loop"):
        return app._in_event_loop
    else:
        return app.IsMainLoopRunning()


def start_event_loop_wx(app=None):
    """Start the wx event loop in a consistent manner."""
    if app is None:
        app = get_app_wx()
    if not is_event_loop_running_wx(app):
        app._in_event_loop = True
        app.MainLoop()
        app._in_event_loop = False
    else:
        app._in_event_loop = True


# -----------------------------------------------------------------------------
# qt4
# -----------------------------------------------------------------------------


def get_app_qt4(*args, **kwargs):
    """Create a new qt4 app or return an existing one."""
    from IPython.external.qt_for_kernel import QtGui

    app = QtGui.QApplication.instance()
    if app is None:
        if not args:
            args = ([""],)
        app = QtGui.QApplication(*args, **kwargs)
    return app


def is_event_loop_running_qt4(app=None):
    """Is the qt4 event loop running."""
    # New way: check attribute on shell instance
    ip = get_ipython()
    if ip is not None:
        return ip.active_eventloop and ip.active_eventloop.startswith("qt")

    # Old way: check attribute on QApplication singleton
    if app is None:
        app = get_app_qt4([""])
    if hasattr(app, "_in_event_loop"):
        return app._in_event_loop
    else:
        # Does qt4 provide a other way to detect this?
        return False


def start_event_loop_qt4(app=None):
    """Start the qt4 event loop in a consistent manner."""
    if app is None:
        app = get_app_qt4([""])
    if not is_event_loop_running_qt4(app):
        app._in_event_loop = True
        app.exec_()
        app._in_event_loop = False
    else:
        app._in_event_loop = True


# -----------------------------------------------------------------------------
# Tk
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# gtk
# -----------------------------------------------------------------------------
