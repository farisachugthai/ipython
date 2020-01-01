"""Terminal input and output prompts.

TMK this is made configurable in the .ipapp module.
"""
import abc
import sys

from prompt_toolkit.formatted_text import PygmentsTokens, fragment_list_width
from prompt_toolkit.shortcuts import print_formatted_text
from pygments.token import Token

from IPython.core.displayhook import DisplayHook
from IPython.core.getipython import get_ipython

from prompt_toolkit.formatted_text import fragment_list_width, PygmentsTokens
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text import fragment_list_width, PygmentsTokens
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.enums import EditingMode

class Prompts:

    # This might be useful to hang onto.
    old_displayhook = sys.displayhook

    def __init__(self, shell=None):
        self.shell = shell or get_ipython()

    @property
    def _is_vi_mode(self):
        if getattr(self.shell.pt_app, "editing_mode", None):
            if self.shell.pt_app.editing_mode == "VI":
                return True

    def better_vi_mode(self, prefix=None, suffix=None):
        """Because it was bothering me the other way that this is setup.

        Add prefix and suffix so the user can configure their prompt with
        strings I don't know why that got deprecated.
    def vi_mode(self):
        if (getattr(self.shell.pt_app, 'editing_mode', None) == 'VI'
                and self.shell.prompt_includes_vi_mode):
            return '['+str(self.shell.pt_app.app.vi_state.input_mode)[3:6]+'] '
        return ''
    def vi_mode(self):
        if (getattr(self.shell.pt_app, 'editing_mode', None) == EditingMode.VI
                and self.shell.prompt_includes_vi_mode):
            mode = str(self.shell.pt_app.app.vi_state.input_mode)
            if mode.startswith('InputMode.'):
                mode = mode[10:13].lower()
            elif mode.startswith('vi-'):
                mode = mode[3:6]
            return '['+mode+'] '
        return ''

        """
        if self._is_vi_mode:
            return prefix + "[" + self.shell.pt_app.editing_mode + "]" + suffix

    def vi_mode(self):
        if (
            getattr(self.shell.pt_app, "editing_mode", None) == "VI"
            and self.shell.prompt_includes_vi_mode
        ):
            return "[" + str(self.shell.pt_app.app.vi_state.input_mode)[3:6] + "] "
        return ""

    def in_prompt_tokens(self):
        return [
            (Token.Prompt, self.vi_mode()),
            (Token.Prompt, "In ["),
            (Token.PromptNum, str(self.shell.execution_count)),
            (Token.Prompt, "]: "),
        ]

    def _width(self):
        return fragment_list_width(self.in_prompt_tokens())

    def continuation_prompt_tokens(self, width=None):
        if width is None:
            width = self._width()
        return [
            (Token.Prompt, (" " * (width - 5)) + "...: "),
        ]

    def rewrite_prompt_tokens(self):
        """

        Returns
        -------

        """
        width = self._width()
        return [
            (Token.Prompt, ("-" * (width - 2)) + "> "),
        ]

    def out_prompt_tokens(self):
        """

        Returns
        -------

        """
        return [
            (Token.OutPrompt, "Out["),
            (Token.OutPromptNum, str(self.shell.execution_count)),
            (Token.OutPrompt, "]: "),
        ]


class ClassicPrompts(Prompts):
    def in_prompt_tokens(self):
        return [
            (Token.Prompt, ">>> "),
        ]

    def continuation_prompt_tokens(self, width=None):
        return [(Token.Prompt, "... ")]

    def rewrite_prompt_tokens(self):
        return []

    def out_prompt_tokens(self):
        return []


class RichPromptDisplayHook(DisplayHook):
    """Subclass of base display hook using coloured prompt"""

    def write_output_prompt(self):
        sys.stdout.write(self.shell.separate_out)
        # If we're not displaying a prompt, it effectively ends with a newline,
        # because the output will be left-aligned.
        self.prompt_end_newline = True

        if self.do_full_cache:
            tokens = self.shell.prompts.out_prompt_tokens()
            prompt_txt = "".join(s for t, s in tokens)
            if prompt_txt and not prompt_txt.endswith("\n"):
                # Ask for a newline before multiline output
                self.prompt_end_newline = False

            if self.shell.pt_app:
                print_formatted_text(
                    PygmentsTokens(tokens), style=self.shell.pt_app.app.style, end="",
                )
            else:
                sys.stdout.write(prompt_txt)

    def write_format_data(self, format_dict, md_dict=None) -> None:
        """

        Parameters
        ----------
        format_dict :
        md_dict :

        Returns
        -------

        """
        if self.shell.mime_renderers:

            for mime, handler in self.shell.mime_renderers.items():
                if mime in format_dict:
                    handler(format_dict[mime], None)
                    return

        super().write_format_data(format_dict, md_dict)


class PromptABC(abc.ABC):
    """For no other reason than the simple fact that I constantly lose track."""

    @abc.abstractmethod
    def in_prompt_tokens(self):
        raise NotImplementedError

    @abc.abstractmethod
    def out_prompt_tokens(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rewrite_prompt_tokens(self):
        raise NotImplementedError

    @abc.abstractmethod
    def continuation_prompt_tokens(self, width=None):
        raise NotImplementedError

    @abc.abstractproperty
    def vi_mode(self):
        """Seriously why isn't it a property. But uh idk if we need to make
        this part of the 'required API' per-se.
        """
        pass
