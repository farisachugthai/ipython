"""
IPython.core.debugger.Pdb.trace_dispatch shall not catch
`bdb.BdbQuit`.

When started through ``__main__`` and an exception happened after hitting "c",
this is needed in order to be able to quit the debugging session (see #9950).

"""
import asyncio
import signal
import sys

from prompt_toolkit import __version__ as ptk_version
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.filters import (
    Condition,
    emacs_insert_mode,
    has_focus,
    has_selection,
    vi_insert_mode,
)
from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit.key_binding import KeyBindings

# Nov 27, 2019: Just added this
from prompt_toolkit.key_binding.bindings.basic import load_basic_bindings
from prompt_toolkit.key_binding.bindings.completion import (
    display_completions_like_readline,
)
from prompt_toolkit.shortcuts.prompt import PromptSession
from pygments.token import Token

from IPython.core.completer import IPCompleter
from IPython.core.debugger import CorePdb as Pdb
from IPython.terminal.ptutils import IPythonPTCompleter
from IPython.terminal.shortcuts import cursor_in_leading_ws, suspend_to_bg

PTK3 = ptk_version.startswith("3.")


class TerminalPdb(Pdb):
    """Standalone IPython debugger."""

    def __init__(self, _ptcomp=None, kb=None, *args, **kwargs):
        """Refactored to encourage visibility in parameters.

        Parameters
        ----------
        _ptcomp : Completer, optional
            If None, defaults to IPCompleter
        kb : KeyBindings, optional
            Defaults to standard IPython keybindings if None.

        """
        super().__init__(self, *args, **kwargs)
        self.pt_comp = pt_comp or None
        self.pt_init()

        self.kb = kb or self.setup_prompt_keybindings()

        options = dict(
            message=(lambda: PygmentsTokens(get_prompt_tokens())),
            editing_mode=getattr(EditingMode, self.shell.editing_mode.upper()),
            key_bindings=kb,
            history=self.shell.debugger_history,
            completer=self._ptcomp,
            enable_history_search=True,
            mouse_support=self.shell.mouse_support,
            complete_style=self.shell.pt_complete_style,
            style=self.shell.style,
            color_depth=self.shell.color_depth,
        )
        if not PTK3:
            options["inputhook"] = self.shell.inputhook
        self.pt_loop = asyncio.new_event_loop()
        self.pt_app = PromptSession(**options)

    def get_prompt_tokens(self):
        """

        Returns
        -------

        """
        return [(Token.Prompt, self.prompt)]

    def pt_init(self):
        """Refactored to setup the completer."""
        if self._ptcomp is None:
            compl = IPCompleter(
                shell=self.shell,
                namespace=locals(),
                global_namespace=globals(),
                config=self.shell.config,
            )
            self._ptcomp = IPythonPTCompleter(compl)

    def setup_prompt_keybindings(self):
        """Added more bindings."""
        kb = KeyBindings()
        supports_suspend = Condition(lambda: hasattr(signal, "SIGTSTP"))
        kb.add("c-z", filter=supports_suspend)(suspend_to_bg)

        if self.shell.display_completions == "readlinelike":
            kb.add(
                "tab",
                filter=(
                    has_focus(DEFAULT_BUFFER) & ~has_selection & vi_insert_mode
                    | emacs_insert_mode & ~cursor_in_leading_ws
                ),
            )(display_completions_like_readline)

        kb.add(load_basic_bindings())

        return kb

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        Override the same methods from cmd.Cmd to provide prompt toolkit replacement.

        Shouldn't we define the class parameters IE self.intro
        in the init?
        """
        if not self.use_rawinput:
            raise ValueError("Sorry ipdb does not support use_rawinput=False")

        # In order to make sure that asyncio code written in the
        # interactive shell doesn't interfere with the prompt, we run the
        # prompt in a different event loop.
        # If we don't do this, people could spawn coroutine with a
        # while/true inside which will freeze the prompt.

        try:
            old_loop = asyncio.get_event_loop()
        except RuntimeError:
            # This happens when the user used `asyncio.run()`.
            old_loop = None

        self.preloop()

        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro) + "\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    self._ptcomp.ipy_completer.namespace = self.curframe_locals
                    self._ptcomp.ipy_completer.global_namespace = (
                        self.curframe.f_globals
                    )

                    asyncio.set_event_loop(self.pt_loop)
                    self._ptcomp.ipy_completer.global_namespace = (
                        self.curframe.f_globals
                    )
                    try:
                        # reset_current_buffer=True)
                        line = self.pt_app.prompt()
                    except EOFError:
                        line = "EOF"
                        line = "EOF"
                    finally:
                        # Restore the original event loop.
                        asyncio.set_event_loop(old_loop)

                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        except Exception:
            raise


def set_trace(frame=None):
    """Start debugging from `frame`.

    If frame is not specified, debugging starts from caller's frame.
    """
    TerminalPdb().set_trace(frame or sys._getframe().f_back)


if __name__ == "__main__":
    import pdb

    old_trace_dispatch = pdb.Pdb.trace_dispatch
    pdb.Pdb = TerminalPdb
    pdb.Pdb.trace_dispatch = old_trace_dispatch
    pdb.main()
