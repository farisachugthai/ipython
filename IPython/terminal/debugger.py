"""
IPython.core.debugger.Pdb.trace_dispatch shall not catch
`bdb.BdbQuit`. When started through __main__ and an exception
happened after hitting "c", this is needed in order to
be able to quit the debugging session (see #9950).
"""
import signal
import sys

from pygments.token import Token
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import (Condition, has_focus, has_selection,
                                    vi_insert_mode, emacs_insert_mode)
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.completion import display_completions_like_readline
# Nov 27, 2019: Just added this
from prompt_toolkit.key_binding.bindings.basic import load_basic_bindings

from prompt_toolkit.shortcuts.prompt import PromptSession
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import PygmentsTokens

from IPython.core.debugger import CorePdb
from IPython.core.completer import IPCompleter
from .ptutils import IPythonPTCompleter
from .shortcuts import suspend_to_bg, cursor_in_leading_ws


class TerminalPdb(CorePdb):
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
        CorePdb.__init__(self, *args, **kwargs)
        if _ptcomp is not None:
            self._ptcomp = _ptcomp
        else:
            self.pt_init()

        if kb is None:
            kb = self.setup_prompt_keybindings()

        self.pt_app = PromptSession(
            message=(lambda: PygmentsTokens(self.get_prompt_tokens())),
            editing_mode=getattr(EditingMode, self.shell.editing_mode.upper()),
            key_bindings=kb,
            history=self.shell.debugger_history,
            completer=self._ptcomp,
            enable_history_search=True,  # we don't check the shell parameter?
            mouse_support=self.shell.mouse_support,
            complete_style=self.shell.pt_complete_style,
            style=self.shell.style,
            inputhook=self.shell.inputhook,
            color_depth=self.shell.color_depth,
        )

    def get_prompt_tokens(self):
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
        supports_suspend = Condition(lambda: hasattr(signal, 'SIGTSTP'))
        kb.add('c-z', filter=supports_suspend)(suspend_to_bg)

        if self.shell.display_completions == 'readlinelike':
            kb.add('tab',
                   filter=(has_focus(DEFAULT_BUFFER)
                           & ~has_selection
                           & vi_insert_mode | emacs_insert_mode
                           & ~cursor_in_leading_ws
                           ))(display_completions_like_readline)

        kb.add(load_basic_bindings())

        return kb

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        override the same methods from cmd.Cmd to provide prompt toolkit replacement.
        """
        if not self.use_rawinput:
            raise ValueError('Sorry ipdb does not support use_rawinput=False')

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
                    self._ptcomp.ipy_completer.global_namespace = self.curframe.f_globals
                    try:
                        line = self.pt_app.prompt(
                        )  # reset_current_buffer=True)
                    except EOFError:
                        line = 'EOF'
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


if __name__ == '__main__':
    import pdb
    old_trace_dispatch = pdb.Pdb.trace_dispatch
    pdb.Pdb = TerminalPdb
    pdb.Pdb.trace_dispatch = old_trace_dispatch
    pdb.main()
