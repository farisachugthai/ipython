"""IPython terminal interface using prompt_toolkit."""

import os
import sys
from warnings import warn

from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.core.profiledir import ProfileDir, ProfileDirError
from IPython.utils.terminal import toggle_set_term_title, set_term_title, restore_term_title
from IPython.utils.process import abbrev_cwd
from traitlets import (Bool, Unicode, Dict, Integer, observe, Instance, Type,
                       default, Enum, Union, Any, validate)

from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.filters import (HasFocus, Condition, IsDone)
from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.layout.processors import ConditionalProcessor, HighlightMatchingBracketProcessor
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession, CompleteStyle, print_formatted_text
from prompt_toolkit.styles import DynamicStyle, merge_styles
from prompt_toolkit.styles.pygments import style_from_pygments_cls, style_from_pygments_dict

from pygments.styles import get_style_by_name
from pygments.style import Style
from pygments.token import Token

from .magics import TerminalMagics
from .pt_inputhooks import get_inputhook_name_and_func
from .prompts import Prompts, ClassicPrompts, RichPromptDisplayHook
from .shortcuts import create_ipython_shortcuts

DISPLAY_BANNER_DEPRECATED = object()


class _NoStyle(Style):
    pass


_style_overrides_light_bg = {
    Token.Prompt: '#0000ff',
    Token.PromptNum: '#0000ee bold',
    Token.OutPrompt: '#cc0000',
    Token.OutPromptNum: '#bb0000 bold',
}

_style_overrides_linux = {
    Token.Prompt: '#00cc00',
    Token.PromptNum: '#00bb00 bold',
    Token.OutPrompt: '#cc0000',
    Token.OutPromptNum: '#bb0000 bold',
}


def get_default_editor():
    """Check user environment for the editor.

    If :envvar:`EDITOR` doesn't exist, it returns vi on POSIX systems and
    notepad on Windows.

    .. todo:: Why don't we use something in IPython.lib.editorhooks?

    Returns
    -------
    environ_key : str
        os.environ.EDITOR

    """
    try:
        return os.environ['EDITOR']
    except KeyError:
        pass
    except UnicodeError:
        warn("$EDITOR environment variable is not pure ASCII. Using platform "
             "default editor.")

    if os.name == 'posix':
        return 'vi'  # the only one guaranteed to be there!
    else:
        return 'notepad'  # same in Windows!


# conservatively check for tty
# overridden streams can result in things like:
# - sys.stdin = None
# - no isatty method
for _name in ('stdin', 'stdout', 'stderr'):
    _stream = getattr(sys, _name)
    if not _stream or not hasattr(_stream, 'isatty') or not _stream.isatty():
        _is_tty = False
        break
else:
    _is_tty = True

_use_simple_prompt = ('IPY_TEST_SIMPLE_PROMPT' in os.environ) or (not _is_tty)


def black_reformat_handler(text_before_cursor):
    import black
    formatted_text = black.format_str(
        text_before_cursor, mode=black.FileMode())
    if not text_before_cursor.endswith('\n') and formatted_text.endswith('\n'):
        formatted_text = formatted_text[:-1]
    return formatted_text


class TerminalInteractiveShell(InteractiveShell):
    mime_renderers = Dict().tag(config=True)

    space_for_menu = Integer(6,
                             help='Number of line at the bottom of the screen '
                             'to reserve for the completion menu').tag(config=True)

    pt_app = None
    debugger_history = None

    simple_prompt = Bool(_use_simple_prompt,
                         help="""Use `raw_input` for the REPL, without completion and prompt colors.

            Useful when controlling IPython as a subprocess, and piping STDIN/OUT/ERR. Known usage are:
            IPython own testing machinery, and emacs inferior-shell integration through elpy.

            This mode default to `True` if the `IPY_TEST_SIMPLE_PROMPT`
            environment variable is set, or the current terminal is not a tty."""
                         ).tag(config=True)

    @property
    def debugger_cls(self):
        from .debugger import TerminalPdb, Pdb
        return Pdb if self.simple_prompt else TerminalPdb

    confirm_exit = Bool(True,
                        help="""
        Set to confirm when you try to exit IPython with an EOF (Control-D
        in Unix, Control-Z/Enter in Windows). By typing 'exit' or 'quit',
        you can force a direct exit without any confirmation.""",
                        ).tag(config=True)

    # TODO: Would it make more sense to use the
    # prompt_toolkit.enums.EditingMode class here?
    editing_mode = Unicode(
        'emacs',
        help="Shortcut style to use at the prompt. 'vi' or 'emacs'.",
    ).tag(config=True)

    autoformatter = Unicode(None,
                            help="Autoformatter to reformat Terminal code. Can be `'black'` or `None`",
                            allow_none=True
                            ).tag(config=True)

    mouse_support = Bool(
        False,
        help="Enable mouse support in the prompt\n(Note: prevents selecting text with the mouse)"
    ).tag(config=True)

    # We don't load the list of styles for the help string, because loading
    # Pygments plugins takes time and can cause unexpected errors.
    highlighting_style = Union([Unicode('legacy'), Type(klass=Style)],
                               help="""The name or class of a Pygments style to use for syntax
        highlighting. To see available styles, run `pygmentize -L styles`."""
                               ).tag(config=True)

    @validate('editing_mode')
    def _validate_editing_mode(self, proposal):
        if proposal['value'].lower() == 'vim':
            proposal['value'] = 'vi'
        elif proposal['value'].lower() == 'default':
            proposal['value'] = 'emacs'

        if hasattr(EditingMode, proposal['value'].upper()):
            return proposal['value'].lower()

        return self.editing_mode

    @observe('editing_mode')
    def _editing_mode(self, change):
        u_mode = change.new.upper()
        if self.pt_app:
            self.pt_app.editing_mode = u_mode

    @observe('autoformatter')
    def _autoformatter_changed(self, change):
        """Observe the autoformatter parameter of the config dict.

        Parameters
        ----------
        change

        Raises
        ------
        :exc:`ValueError`

        """
        formatter = change.new
        if formatter is None:
            self.reformat_handler = lambda x: x
        elif formatter == 'black':
            self.reformat_handler = black_reformat_handler
        else:
            raise ValueError

    @observe('autoformatter')
    def _autoformatter_changed(self, change):
        formatter = change.new
        if formatter is None:
            self.reformat_handler = lambda x: x
        elif formatter == 'black':
            self.reformat_handler = black_reformat_handler
        else:
            raise ValueError

    @observe('highlighting_style')
    @observe('colors')
    def _highlighting_style_changed(self, change):
        self.refresh_style()

    def refresh_style(self):
        self._style = self._make_style_from_name_or_cls(
            self.highlighting_style)

    highlighting_style_overrides = Dict(
        help="Override highlighting format for specific tokens").tag(
            config=True)

    true_color = Bool(
        False,
        help=("Use 24bit colors instead of 256 colors in prompt highlighting. "
              "If your terminal supports true color, the following command "
              "should print 'TRUECOLOR' in orange: "
              "printf \"\\x1b[38;2;255;100;0mTRUECOLOR\\x1b[0m\\n\"")).tag(
                  config=True)

    editor = Unicode(
        get_default_editor(),
        help="Set the editor used by IPython (default to $EDITOR/vi/notepad)."
    ).tag(config=True)

    prompts_class = Type(
        Prompts,
        help='Class used to generate Prompt token for prompt_toolkit').tag(
            config=True)

    prompts = Instance(Prompts)

    @default('prompts')
    def _prompts_default(self):
        return self.prompts_class(self)

    @default('displayhook_class')
    def _displayhook_class_default(self):
        return RichPromptDisplayHook

    term_title = Bool(
        True, help="Automatically set the terminal title").tag(config=True)

    term_title_format = Unicode(
        "IPython: {cwd}",
        help="Customize the terminal title format.  This is a python format string. "
        + "Available substitutions are: {cwd}.").tag(config=True)

    display_completions = Enum(
        ('column', 'multicolumn', 'readlinelike'),
        help=("Options for displaying tab completions, 'column', 'multicolumn', and "
              "'readlinelike'. These options are for `prompt_toolkit`, see "
              "`prompt_toolkit` documentation for more information."),
        default_value='multicolumn').tag(config=True)

    highlight_matching_brackets = Bool(
        True,
        help="Highlight matching brackets.",
    ).tag(config=True)

    extra_open_editor_shortcuts = Bool(
        False,
        help="Enable vi (v) or Emacs (C-X C-E) shortcuts to open an external editor. "
        "This is in addition to the F2 binding, which is always enabled.").tag(
            config=True)

    handle_return = Any(
        None,
        help="Provide an alternative handler to be called when the user presses "
        "Return. This is an advanced option intended for debugging, which "
        "may be changed or removed in later releases.").tag(config=True)

    enable_history_search = Bool(
        True,
        help="Allows to enable/disable the prompt toolkit history search").tag(
            config=True)

    prompt_includes_vi_mode = Bool(
        True,
        help="Display the current vi mode (when using vi editing mode).").tag(
            config=True)

    @observe('term_title')
    def init_term_title(self, change=None):
        # Enable or disable the terminal title.
        if self.term_title:
            toggle_set_term_title(True)
            set_term_title(self.term_title_format.format(cwd=abbrev_cwd()))
        else:
            toggle_set_term_title(False)

    def restore_term_title(self):
        if self.term_title:
            restore_term_title()

    def init_display_formatter(self):
        """We don't need to keep making weird ass super calls. Move to init?"""
        super().init_display_formatter()
        # terminal only supports plain text
        self.display_formatter.active_types = ['text/plain']
        # disable `_ipython_display_`
        self.display_formatter.ipython_display_formatter.enabled = False

    def init_prompt_toolkit_cli(self):
        """The entry point for prompt_toolkit!

        Originally didn't have a docstring so easy to over look but this is a
        really important method here.
        """
        if self.simple_prompt:
            # Fall back to plain non-interactive output for tests.
            # This is very limited.
            def prompt():
                prompt_text = "".join(x[1]
                                      for x in self.prompts.in_prompt_tokens())
                lines = [input(prompt_text)]
                prompt_continuation = "".join(
                    x[1] for x in self.prompts.continuation_prompt_tokens())
                while self.check_complete('\n'.join(lines))[0] == 'incomplete':
                    lines.append(input(prompt_continuation))
                return '\n'.join(lines)

            self.prompt_for_code = prompt
            return

        # Set up keyboard shortcuts
        key_bindings = create_ipython_shortcuts(self)

        # Pre-populate history from IPython's history database
        history = InMemoryHistory()
        last_cell = u""
        for __, ___, cell in self.history_manager.get_tail(
                self.history_load_length, include_latest=True):
            # Ignore blank lines and consecutive duplicates
            cell = cell.rstrip()
            if cell and (cell != last_cell):
                history.append_string(cell)
                last_cell = cell

        self._style = self._make_style_from_name_or_cls(
            self.highlighting_style)
        self.style = DynamicStyle(lambda: self._style)

        editing_mode = getattr(EditingMode, self.editing_mode.upper())

        from .ptutils import IPythonPTCompleter

        self.pt_app = PromptSession(
            editing_mode=editing_mode,
            key_bindings=key_bindings,
            history=history,
            completer=IPythonPTCompleter(shell=self),
            enable_history_search=self.enable_history_search,
            style=self.style,
            include_default_pygments_style=False,
            mouse_support=self.mouse_support,
            enable_open_in_editor=self.extra_open_editor_shortcuts,
            color_depth=self.color_depth,
            **self._extra_prompt_options())

    def _make_style_from_name_or_cls(self, name_or_cls):
        """Small wrapper that make an IPython compatible style from a style name.

        We need that to add style for prompt ... etc.
        """
        style_overrides = {}
        if name_or_cls == 'legacy':
            legacy = self.colors.lower()
            if legacy == 'linux':
                style_cls = get_style_by_name('monokai')
                style_overrides = _style_overrides_linux
            elif legacy == 'lightbg':
                style_overrides = _style_overrides_light_bg
                style_cls = get_style_by_name('pastie')
            elif legacy == 'neutral':
                # The default theme needs to be visible on both a dark background
                # and a light background, because we can't tell what the terminal
                # looks like. These tweaks to the default theme help with that.
                style_cls = get_style_by_name('default')
                style_overrides.update({
                    Token.Number: '#007700',
                    Token.Operator: 'noinherit',
                    Token.String: '#BB6622',
                    Token.Name.Function: '#2080D0',
                    Token.Name.Class: 'bold #2080D0',
                    Token.Name.Namespace: 'bold #2080D0',
                    Token.Prompt: '#009900',
                    Token.PromptNum: '#ansibrightgreen bold',
                    Token.OutPrompt: '#990000',
                    Token.OutPromptNum: '#ansibrightred bold',
                })

                # Hack: Due to limited color support on the Windows console
                # the prompt colors will be wrong without this
                if os.name == 'nt':
                    style_overrides.update({
                        Token.Prompt: '#ansidarkgreen',
                        Token.PromptNum: '#ansigreen bold',
                        Token.OutPrompt: '#ansidarkred',
                        Token.OutPromptNum: '#ansired bold',
                    })
            elif legacy == 'nocolor':
                style_cls = _NoStyle
            # hold up how is this missing from master
            # elif legacy == 'nocolor':
            #     style_cls = _NoStyle

                style_overrides = {}
            else:
                raise ValueError('Got unknown colors: ', legacy)
        else:
            if isinstance(name_or_cls, str):
                style_cls = get_style_by_name(name_or_cls)
            else:
                style_cls = name_or_cls

            style_overrides = {
                Token.Prompt: '#009900',
                Token.PromptNum: '#ansibrightgreen bold',
                Token.OutPrompt: '#990000',
                Token.OutPromptNum: '#ansibrightred bold',
            }
        style_overrides.update(self.highlighting_style_overrides)
        style = merge_styles([
            style_from_pygments_cls(style_cls),
            style_from_pygments_dict(style_overrides),
        ])

        return style

    @property
    def pt_complete_style(self):
        return {
            'multicolumn': CompleteStyle.MULTI_COLUMN,
            'column': CompleteStyle.COLUMN,
            'readlinelike': CompleteStyle.READLINE_LIKE,
        }[self.display_completions]

    @property
    def color_depth(self):
        """ return (ColorDepth.TRUE_COLOR if self.true_color else None)."""
        return ColorDepth.TRUE_COLOR if self.true_color else None

    def _extra_prompt_options(self):
        """Return the current layout option for the current InteractiveShell."""

        def get_message():
            """return PygmentsTokens(self.prompts.in_prompt_tokens())."""
            return PygmentsTokens(self.prompts.in_prompt_tokens())

        from .ptutils import IPythonPTLexer
        if self.editing_mode == 'emacs':
            # with emacs mode the prompt is (usually) static, so we call only
            # the function once. With VI mode it can toggle between [ins] and
            # [nor] so we can't precompute.
            # here I'm going to favor the default keybinding which almost
            # everybody uses to decrease CPU usage.
            # if we have issues with users with custom Prompts we can see how to
            # work around this.
            get_message = get_message()

        return {
            'complete_in_thread': False,
            'lexer': IPythonPTLexer(),
            'reserve_space_for_menu': self.space_for_menu,
            'message': get_message,
            'prompt_continuation': (
                lambda width, lineno, is_soft_wrap:
                PygmentsTokens(self.prompts.continuation_prompt_tokens(width))),
            'multiline': True,
            'complete_style': self.pt_complete_style,

            # Highlight matching brackets, but only when this setting is
            # enabled, and only when the DEFAULT_BUFFER has the focus.
            'input_processors': [
                ConditionalProcessor(
                    processor=HighlightMatchingBracketProcessor(
                        chars='[](){}'),
                    filter=HasFocus(DEFAULT_BUFFER) & ~IsDone()
                    & Condition(lambda: self.highlight_matching_brackets))],
            'inputhook': self.inputhook,
        }

    def prompt_for_code(self):
        if self.rl_next_input:
            default = self.rl_next_input
            self.rl_next_input = None
        else:
            default = ''

        with patch_stdout(raw=True):
            text = self.pt_app.prompt(
                default=default,
                # pre_run=self.pre_prompt,# reset_current_buffer=True,
                **self._extra_prompt_options())
        return text

    def init_io(self):
        """Literally only imports colorama if sys.platform==win32 or cli.

        Got rid of it in the superclass as well. Both invoke classes we got rid
        of and nothing else.
        """
        # if sys.platform not in {'win32', 'cli'}:
        #     return
        # import colorama
        # colorama.init()

    def init_magics(self):
        super().init_magics()
        self.register_magics(TerminalMagics)

    def init_alias(self):
        """The parent class defines aliases that can be safely used with any
        frontend.

        After calling the super method.

        Now define aliases that only make sense on the terminal, because they
        need direct access to the console in a way that we can't emulate in
        GUI or web frontend.

        Gotta admit I'm very confused why this code exists at all though.::

        """
        super().init_alias()

        if os.name == 'posix':
            for cmd in ('clear', 'more', 'less', 'man'):
                self.alias_manager.soft_define_alias(cmd, cmd)

    def __init__(self, *args, **kwargs):
        """Why is this class built so that every individual method calls it's super?

        Added init_profile_dir because that felt important. It's in the super class.

        Notes
        -----
        The super call is totally required.

        """
        super().__init__(*args, **kwargs)
        self.init_prompt_toolkit_cli()
        self.init_term_title()
        self.keep_running = True
        self.init_profile_dir()
        self.debugger_history = InMemoryHistory()

    def ask_exit(self):
        self.keep_running = False

    rl_next_input = None

    def interact(self):
        """An oddly undocumented method.

        When running this is the method that calls a lot of the mixin classes'
        methods. For example, this will initiate ``run_code``.

        Also of all the places to have no try/excepts, our self.run_code
        block DEFINITELY should have one.
        """

        self.keep_running = True
        while self.keep_running:
            print(self.separate_in, end='')

            try:
                code = self.prompt_for_code()
            except EOFError:
                self.check_exit()

            else:
                if code:
                    try:
                        self.run_cell(code, store_history=True)
                    except KeyboardInterrupt:
                        self.log.warning('Interrupted!')
                    except EOFError:
                        self.check_exit()
                    except ModuleNotFoundError:
                        self.log.error('Error: Module Not Found!')
                    except OSError as e:
                        self.log.error('Error: {}'.format(e.__traceback__))
                    except BaseException as e:
                        self.log.warning(e)

    def check_exit(self):
        """A quicker way of checking if the user really wants to exit."""
        if (not self.confirm_exit) \
                or self.ask_yes_no('Do you really want to exit ([y]/n)?', 'y', 'n'):
            self.ask_exit()

    def mainloop(self, display_banner=DISPLAY_BANNER_DEPRECATED):
        """I think this is the method to drives the whole application.

        It calls ``while True:: self.interact()`` which seems like it.

        Parameters
        -----------
        DISPLAY_BANNER_DEPRECATED : str
            Deprecated parameter don't worry about it.

        """
        # An extra layer of protection in case someone mashing Ctrl-C breaks
        # out of our internal code.
        if display_banner is not DISPLAY_BANNER_DEPRECATED:
            warn(
                'mainloop `display_banner` argument is deprecated since IPython 5.0. Call `show_banner()` if needed.',
                DeprecationWarning,
                stacklevel=2)
        while True:
            try:
                self.interact()
                break
            except KeyboardInterrupt as e:
                print("\n%s escaped interact()\n" % type(e).__name__)
            finally:
                # An interrupt during the eventloop will mess up the
                # internal state of the prompt_toolkit library.
                # Stopping the eventloop fixes this, see
                # https://github.com/ipython/ipython/pull/9867
                if hasattr(self, '_eventloop'):
                    self._eventloop.stop()

                self.restore_term_title()

    _inputhook = None

    def inputhook(self, context):
        if self._inputhook is not None:
            self._inputhook(context)

    active_eventloop = None

    def enable_gui(self, gui=None):
        if gui and (gui != 'inline'):
            self.active_eventloop, self._inputhook =\
                get_inputhook_name_and_func(gui)
        else:
            self.active_eventloop = self._inputhook = None

    # Run !system commands directly, not through pipes, so terminal programs
    # work correctly.
    system = InteractiveShell.system_raw

    def auto_rewrite_input(self, cmd):
        """Overridden from the parent class to use fancy rewriting prompt.

        Parameters
        ----------
        cmd : str
            Tokens to print for the new prompt.

        Notes
        ------
        Probably worth mentioning to anyone implementing a modified
        :class:`~IPython.terminal.prompts.Prompts` class that this method
        expects the new class to have a method
        :meth:`~prompts.rewrite_prompt_tokens`.

        """
        if not self.show_rewritten_input:
            return

        tokens = self.prompts.rewrite_prompt_tokens()
        if self.pt_app:
            print_formatted_text(PygmentsTokens(tokens), end='',
                                 style=self.pt_app.app.style)
            print(cmd)
        else:
            prompt = ''.join(s for t, s in tokens)
            print(prompt, cmd, sep='')

    _prompts_before = None

    @staticmethod
    def execfile(self, fname, globs, locs=None):
        """Nabbed from the setup.py. Honestly it's surprising that we don't have these sitting around."""
        locs = locs or globs
        with open(fname) as f:
            exec(compile(f.read(), fname, "exec"), globs, locs)

    def switch_doctest_mode(self, mode):
        """Switch prompts to classic for %doctest_mode"""
        if mode:
            self._prompts_before = self.prompts
            self.prompts = ClassicPrompts(self)
        elif self._prompts_before:
            self.prompts = self._prompts_before
            self._prompts_before = None

    def __repr__(self):
        return ''.join(self.__class__.__name__)

    def init_profile_dir(self, profile_dir=None):
        """Modify this so we have a none argument for profile_dir."""
        if profile_dir is not None:
            self.profile_dir = profile_dir
            return
        try:
            self.profile_dir = ProfileDir.create_profile_dir_by_name(self.ipython_dir, 'default')
        except ProfileDirError:
            self.log.error('Profiledirerror')
        except BaseException as e:
            self.log.warning(e)

InteractiveShellABC.register(TerminalInteractiveShell)


if __name__ == '__main__':
    TerminalInteractiveShell.instance().interact()
