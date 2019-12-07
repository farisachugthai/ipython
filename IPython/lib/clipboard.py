"""Utilities for accessing the platform's clipboard.

Yo honestly the implementation for this is outrageously shoddy but only
shows up in %paste or %cpaste {*i forget which right now but it's oddly not
both*}.

We should try coming up with some kind of shim and then we can get delete
this too.

"""
import subprocess

from IPython.core.error import TryNext, ClipboardEmpty


def win32_clipboard_get():
    """Get the current clipboard's text on Windows.

    Requires Mark Hammond's pywin32 extensions.
    """
    try:
        import win32clipboard
    except ImportError:
        raise TryNext(
            "Getting text from the clipboard requires the pywin32 "
            "extensions: http://sourceforge.net/projects/pywin32/"
        )
    win32clipboard.OpenClipboard()
    try:
        text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    except (TypeError, win32clipboard.error):
        try:
            text = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
        except (TypeError, win32clipboard.error):
            raise ClipboardEmpty
    finally:
        win32clipboard.CloseClipboard()
    return text


def osx_clipboard_get():
    """ Get the clipboard's text on OS X.
    """
    p = subprocess.Popen(["pbpaste", "-Prefer", "ascii"], stdout=subprocess.PIPE)
    text, stderr = p.communicate()
    # Text comes in with old Mac \r line endings. Change them to \n.
    text = text.replace(b"\r", b"\n")
    return text


def tkinter_clipboard_get():
    """Get the clipboard's text using Tkinter.

    This is the default on systems that are not Windows or OS X. It may
    interfere with other UI toolkits and should be replaced with an
    implementation that uses that toolkit.
    """
    try:
        from tkinter import Tk, TclError
    except ImportError:
        raise TryNext(
            "Getting text from the clipboard on this platform requires tkinter."
        )

    root = Tk()
    root.withdraw()
    try:
        text = root.clipboard_get()
    except TclError:
        raise ClipboardEmpty
    finally:
        root.destroy()
    return text
