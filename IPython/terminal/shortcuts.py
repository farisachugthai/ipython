"""Module to define and register Terminal IPython shortcuts.

Heavily utilizes :mod:`prompt_toolkit`.


"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import warnings
import signal
import sys
from typing import Callable

from IPython.core.getipython import get_ipython

from prompt_toolkit.application.current import get_app
from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER
from prompt_toolkit.filters import (
    has_focus,
    has_selection,
    Condition,
    vi_insert_mode,
    emacs_insert_mode,
    has_completions,
    vi_mode,
)
from prompt_toolkit.key_binding.bindings.completion import (
    display_completions_like_readline,
)
from prompt_toolkit.key_binding import KeyBindings


class VerbosePrompt:
    """Because I can't ever remember how these classes resolve."""

    def __init__(self):
        self.shell = get_ipython()
        if getattr(self.shell, "pt_app", None):
            self.app = self.shell.pt_app
            self.buffer = self.shell.pt_app.buffer
            self.document = self.shell.pt_app.buffer.document

    def __repr__(self):
        return "{}".format(i for i in dir(self) if not i.startswith("_"))


@Condition
def cursor_in_leading_ws():
    """

    Returns
    -------

    """
    before = get_app().current_buffer.document.current_line_before_cursor
    return (not before) or before.isspace()


def create_ipython_shortcuts(shell):
    """Set up the prompt_toolkit keyboard shortcuts for IPython.

    It's kinda frustrating that this isn't configurable at all. It's left as
    an exercise for the user to figure out how to override this and even then
    it's a pretty manual and brute-force approach.

    Should really figure something out for this.
    """

    kb = KeyBindings()
    insert_mode = vi_insert_mode | emacs_insert_mode

    if getattr(shell, "handle_return", None):
        return_handler = shell.handle_return(shell)
    else:
        return_handler = newline_or_execute_outer(shell)

    kb.add("enter", filter=(has_focus(DEFAULT_BUFFER) & ~has_selection & insert_mode))(
        return_handler
    )

    def reformat_and_execute(event):
        """

        Parameters
        ----------
        event :
        """
        reformat_text_before_cursor(
            event.current_buffer, event.current_buffer.document, shell
        )
        event.current_buffer.validate_and_handle()

    kb.add(
        "escape",
        "enter",
        filter=(has_focus(DEFAULT_BUFFER) & ~has_selection & insert_mode),
    )(reformat_and_execute)

    kb.add("c-\\")(force_exit)

    kb.add("c-p", filter=(vi_insert_mode & has_focus(DEFAULT_BUFFER)))(
        previous_history_or_previous_completion
    )

    kb.add("c-n", filter=(vi_insert_mode & has_focus(DEFAULT_BUFFER)))(
        next_history_or_next_completion
    )

    kb.add("c-g", filter=(has_focus(DEFAULT_BUFFER) & has_completions))(
        dismiss_completion
    )

    kb.add("c-c", filter=has_focus(DEFAULT_BUFFER))(reset_buffer)

    kb.add("c-c", filter=has_focus(SEARCH_BUFFER))(reset_search_buffer)

    supports_suspend = Condition(lambda: hasattr(signal, "SIGTSTP"))
    kb.add("c-z", filter=supports_suspend)(suspend_to_bg)

    # Ctrl+I == Tab
    kb.add(
        "tab",
        filter=(
            has_focus(DEFAULT_BUFFER)
            & ~has_selection
            & insert_mode
            & cursor_in_leading_ws
        ),
    )(indent_buffer)
    kb.add("c-o", filter=(has_focus(DEFAULT_BUFFER) & emacs_insert_mode))(
        newline_autoindent_outer(shell.input_transformer_manager)
    )

    kb.add("f2", filter=has_focus(DEFAULT_BUFFER))(open_input_in_editor)

    if shell.display_completions == "readlinelike":
        kb.add(
            "c-i",
            filter=(
                has_focus(DEFAULT_BUFFER)
                & ~has_selection
                & insert_mode
                & ~cursor_in_leading_ws
            ),
        )(display_completions_like_readline)

    if sys.platform == "win32":
        kb.add("c-v", filter=(has_focus(DEFAULT_BUFFER) & ~vi_mode))(win_paste)

    return kb


def reformat_text_before_cursor(buffer, document, shell):
    """

    Parameters
    ----------
    buffer :
    document :
    shell :
    """
    text = buffer.delete_before_cursor(len(document.text[: document.cursor_position]))
    try:
        formatted_text = shell.reformat_handler(text)
        buffer.insert_text(formatted_text)
    except Exception as e:
        buffer.insert_text(text)


def newline_or_execute_outer(shell):
    """Admittedly there's a LOT going on and this probably should be broken up."""

    def newline_or_execute(event):
        """When the user presses return, insert a newline or execute the code."""
        b = event.current_buffer
        d = b.document

        if b.complete_state:
            cc = b.complete_state.current_completion
            if cc:
                b.apply_completion(cc)
            else:
                b.cancel_completion()
            return

        # If there's only one line, treat it as if the cursor is at the end.
        # See https://github.com/ipython/ipython/issues/10425
        if d.line_count == 1:
            check_text = d.text
        else:
            check_text = d.text[: d.cursor_position]
        status, indent = shell.check_complete(check_text)

        # if all we have after the cursor is whitespace: reformat current text
        # before cursor
        after_cursor = d.text[d.cursor_position:]
        if not after_cursor.strip():
            reformat_text_before_cursor(b, d, shell)

        if not (
            d.on_last_line
            or d.cursor_position_row >= d.line_count - d.empty_line_count_at_the_end()
        ):
            if shell.autoindent:
                b.insert_text("\n" + indent)
            else:
                b.insert_text("\n")
            return

        if (status != "incomplete") and b.accept_handler:
            reformat_text_before_cursor(b, d, shell)
            b.validate_and_handle()
        else:
            if shell.autoindent:
                b.insert_text("\n" + indent)
            else:
                b.insert_text("\n")

    return newline_or_execute


def previous_history_or_previous_completion(event):
    """
    Control-P in vi edit mode on readline is history next, unlike default prompt toolkit.

    If completer is open this still select previous completion.
    """
    event.current_buffer.auto_up()


def next_history_or_next_completion(event):
    """
    Control-N in vi edit mode on readline is history previous, unlike default prompt toolkit.

    If completer is open this still select next completion.
    """
    event.current_buffer.auto_down()


def dismiss_completion(event):
    """

    Parameters
    ----------
    event :
    """
    b = event.current_buffer
    if b.complete_state:
        b.cancel_completion()


def reset_buffer(event):
    """

    Parameters
    ----------
    event :
    """
    b = event.current_buffer
    if b.complete_state:
        b.cancel_completion()
    else:
        b.reset()


def reset_search_buffer(event):
    """

    Parameters
    ----------
    event :
    """
    if event.current_buffer.document.text:
        event.current_buffer.reset()
    else:
        event.app.layout.focus(DEFAULT_BUFFER)


def suspend_to_bg(event):
    """

    Parameters
    ----------
    event :
    """
    event.app.suspend_to_background()


def force_exit(event):
    """Force exit (with a non-zero return value)."""
    sys.exit("Quit")


def indent_buffer(event):
    """

    Parameters
    ----------
    event :
    """
    event.current_buffer.insert_text(" " * 4)


def newline_autoindent_outer(inputsplitter) -> Callable[..., None]:
    """
    Return a function suitable for inserting a indented newline after the cursor.

    Fancier version of deprecated ``newline_with_copy_margin`` which should
    compute the correct indentation of the inserted line. That is to say, indent
    by 4 extra space after a function definition, class definition, context
    manager... And dedent by 4 space after ``pass``, ``return``, ``raise ...``.
    """

    def newline_autoindent(event):
        """insert a newline after the cursor indented appropriately."""
        b = event.current_buffer
        d = b.document

        if b.complete_state:
            b.cancel_completion()
        text = d.text[: d.cursor_position] + "\n"
        _, indent = inputsplitter.check_complete(text)
        b.insert_text("\n" + (" " * (indent or 0)), move_cursor=False)

    return newline_autoindent


def open_input_in_editor(event):
    """

    Parameters
    ----------
    event :
    """
    event.app.current_buffer.tempfile_suffix = ".py"
    event.app.current_buffer.open_in_editor()


if sys.platform == "win32":
    from IPython.core.error import TryNext
    from IPython.lib.clipboard import (
        ClipboardEmpty,
        win32_clipboard_get,
        tkinter_clipboard_get,
    )

    def win_paste(event):
        """

        Parameters
        ----------
        event :

        Returns
        -------

        """
        try:
            text = win32_clipboard_get()
        except TryNext:
            try:
                text = tkinter_clipboard_get()
            except (TryNext, ClipboardEmpty):
                return
        except ClipboardEmpty:
            return
        event.current_buffer.insert_text(text.replace("\t", " " * 4))
