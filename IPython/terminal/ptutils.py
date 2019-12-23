""":mod:`prompt_toolkit` utilities.

Everything in this module is a private API, not to be used outside IPython.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import keyword
import os
import re

import unicodedata
from wcwidth import wcwidth

from traitlets.config.application import TraitError
from IPython.core.getipython import get_ipython

# So how does __all__ work is a relevant question I have now...
# We import things from IPython.core.completer that aren't in all. Or is this
# code never executed? Or it fails silently?
from IPython.core._completer import (
    provisionalcompleter,
    cursor_to_position,
    _deduplicate_completions,
)

from IPython.lib.lexers import IPyLexer


from prompt_toolkit.completion import (
    CompleteEvent,
    FuzzyWordCompleter,
    NestedCompleter,
    PathCompleter,
    WordCompleter,
)
from prompt_toolkit.document import Document

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.patch_stdout import patch_stdout

# import pygments.lexers as pygments_lexers
import pygments

# just saying some of these could be real cool
# from pygments.lexers.other import SqliteConsoleLexer

_completion_sentinel = object()


def _elide(string, *, min_elide=30):
    """
    If a string is long enough, and has at least 3 dots,
    replace the middle part with ellipses.

    If a string naming a file is long enough, and has at least 3 slashes,
    replace the middle part with ellipses.

    If three consecutive dots, or two consecutive dots are encountered these are
    replaced by the equivalents HORIZONTAL ELLIPSIS or TWO DOT LEADER unicode
    equivalents
    """
    string = string.replace("...", "\N{HORIZONTAL ELLIPSIS}")
    string = string.replace("..", "\N{TWO DOT LEADER}")
    if len(string) < min_elide:
        return string

    object_parts = string.split(".")
    file_parts = string.split(os.sep)

    if len(object_parts) > 3:
        return "{}.{}\N{HORIZONTAL ELLIPSIS}{}.{}".format(
            object_parts[0], object_parts[1][0], object_parts[-2][-1],
            object_parts[-1])

    elif len(file_parts) > 3:
        return ("{}" + os.sep + "{}\N{HORIZONTAL ELLIPSIS}{}" + os.sep +
                "{}").format(file_parts[0], file_parts[1][0],
                             file_parts[-2][-1], file_parts[-1])

    return string


def _adjust_completion_text_based_on_context(text, body, offset):
    if text.endswith("=") and len(body) > offset and body[offset] == "=":
        return text[:-1]
    else:
        return text


class SimpleWordCompletions:
    def __init__(self, shell):
        self.shell = shell or get_ipython()
        self._initialize_word_completer()

    @property
    def user_ns(self):
        return self.shell.user_ns

    def _initialize_word_completer(self, *args, **kwargs):
        if not args and not kwargs:
            self.word_completer = WordCompleter(
                self.user_ns, pattern=re.compile(r"^([a-zA-Z0-9_.]+|[^a-zA-Z0-9_.\s]+)")
            )
        # TODO: else:

    def get_document(self):
        """Is this how you do this?"""
        return self.shell.pt_app.app.current_buffer.document

    def get_completions(self, doc=None, complete_event=None, **kwargs):

        if doc is None:
            doc = self.get_document()
        yield WordCompleter.get_completions(
            document=doc, complete_event=CompleteEvent(), **kwargs
        )


def get_path_completer():
    """Basically took this from Jon's unit tests."""
    return PathCompleter(min_input_len=1, expanduser=True)


def get_keyword_completer():
    """Return all valid Python keywords."""
    return WordCompleter(
        keyword.kwlist, pattern=re.compile(r"^([a-zA-Z0-9_.]+|[^a-zA-Z0-9_.\s]+)")
    )


class IPythonPTCompleter(Completer):
    """Adaptor to provide IPython completions to prompt_toolkit"""

    def __init__(self, ipy_completer=None, shell=None, *args, **kwargs):
        if shell is None and ipy_completer is None:
            # raise TypeError("Please pass shell=an InteractiveShell instance.")
            # why can't we do this? all the machinery is up and moving
            shell = get_ipython()
            if shell is None:  # okay NOW we have to start worrying
                raise TraitError
        self._ipy_completer = ipy_completer
        self.shell = shell
        super().__init__(*args, **kwargs)

    @property
    def ipy_completer(self):
        """

        Returns
        -------

        """
        if self._ipy_completer:
            return self._ipy_completer
        else:
            return self.shell.Completer

    def get_completions(self, document, complete_event):
        """

        Parameters
        ----------
        document :
        complete_event :

        Returns
        -------

        """
        if not document.current_line.strip():
            return
        # Some bits of our completion system may print stuff (e.g. if a module
        # is imported). This context manager ensures that doesn't interfere with
        # the prompt.

        with patch_stdout(), provisionalcompleter():
            body = document.text
            cursor_row = document.cursor_position_row
            cursor_col = document.cursor_position_col
            cursor_position = document.cursor_position
            offset = cursor_to_position(body, cursor_row, cursor_col)
            yield from self._get_completions(body, offset, cursor_position,
                                             self.ipy_completer)

    @staticmethod
    def _get_completions(body, offset, cursor_position, ipyc):
        """
        Private equivalent of get_completions() use only for unit_testing.
        """
        debug = getattr(ipyc, "debug", False)
        completions = _deduplicate_completions(body,
                                               ipyc.completions(body, offset))
        for c in completions:
            if not c.text:
                # Guard against completion machinery giving us an empty string.
                continue
            text = unicodedata.normalize("NFC", c.text)
            # When the first character of the completion has a zero length,
            # then it's probably a decomposed unicode character. E.g. caused by
            # the "\dot" completion. Try to compose again with the previous
            # character.
            if not wcwidth(text[0]):
                if cursor_position + c.start > 0:
                    char_before = body[c.start - 1]
                    fixed_text = unicodedata.normalize("NFC",
                                                       char_before + text)

                    # Yield the modified completion instead, if this worked.
                    if wcwidth(text[0:1]) == 1:
                        yield Completion(fixed_text,
                                         start_position=c.start - offset - 1)
                        continue

            # TODO: Use Jedi to determine meta_text
            # (Jedi currently has a bug that results in incorrect information.)
            # meta_text = ''
            # yield Completion(m, start_position=start_pos,
            #                  display_meta=meta_text)
            display_text = c.text

            adjusted_text = _adjust_completion_text_based_on_context(
                c.text, body, offset)
            if c.type == "function":
                yield Completion(
                    adjusted_text,
                    start_position=c.start - offset,
                    display=_elide(display_text + "()"),
                    display_meta=c.type + c.signature,
                )
            else:
                yield Completion(
                    adjusted_text,
                    start_position=c.start - offset,
                    display=_elide(display_text),
                    display_meta=c.type,
                )


class IPythonPTLexer(Lexer):
    """Wrapper around PythonLexer and BashLexer."""
    def __init__(self):
        """Don't we have lexers?"""
        # l = pygments_lexers
        # omg let's spell this out because idk if those lexers are actually
        # available there
        self.python_lexer = PygmentsLexer(pygments.lexers.python.Python3Lexer)
        self.shell_lexer = PygmentsLexer(pygments.lexers.shell.BashLexer)
        self.ipython_lexer = PygmentsLexer(IPyLexer)
        self.magic_lexers = {
            "HTML": PygmentsLexer(pygments.lexers.html.HtmlLexer),
            "html": PygmentsLexer(pygments.lexers.html.HtmlLexer),
            "javascript":
            PygmentsLexer(pygments.lexers.javascript.JavascriptLexer),
            "js": PygmentsLexer(pygments.lexers.javascript.JavascriptLexer),
            "perl": PygmentsLexer(pygments.lexers.perl.PerlLexer),
            "ruby": PygmentsLexer(pygments.lexers.ruby.RubyLexer),
            "latex": PygmentsLexer(pygments.lexers.markup.TexLexer),
        }

    def lex_document(self, document):
        """

        Parameters
        ----------
        document :

        Returns
        -------

        """
        text = document.text.lstrip()

        if text.startswith("!") or text.startswith("%%bash"):
            lexer = self.shell_lexer

        elif text.startswith("%%"):
            for magic, l in self.magic_lexers.items():
                if text.startswith("%%" + magic):
                    lexer = l
                    break
        else:
            lexer = self.ipython_lexer

        return lexer.lex_document(document)
