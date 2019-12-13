r"""Completion for IPython.

This module started as fork of the :mod:`rlcompleter` module in the Python
standard library.  The original enhancements made to rlcompleter have been
sent upstream and were accepted as of Python 2.3,

This module now support a wide variety of completion mechanism both available
for normal classic Python code, as well as completer for IPython specific
syntax like magics.


Latex and Unicode completion
============================

IPython and compatible frontends not only can complete your code, but can help
you to input a wide range of characters. In particular we allow you to insert
a unicode character using the tab completion mechanism.


Forward latex/unicode completion
--------------------------------

Forward completion allows you to easily type a unicode character using its
latex name, or unicode long description. To do so type a backslash, :kbd:`\`,
followed by the relevant name and press the completion trigger key, :kbd:`Tab`:


Using latex completion:

.. code::

    \\alpha<tab>
    α

or using unicode completion:


.. code::

    \\greek small letter alpha<tab>
    α


Only valid Python identifiers will complete the current line.

After pressing the trigger key, characters such as arrow keys or
dots may also be used. However, they need to be put after their
counterpart which stands in contrast to a system like LaTex.

That is to say, `F\\\\vec<tab>` is correct, not `\\\\vec<tab>F`.

Some browsers are known to display combining characters incorrectly.

Backward latex completion
-------------------------

It is sometime challenging to know how to type a character, if you are using
IPython, or any compatible frontend you can prepend backslash to the character
and press `<tab>` to expand it to its latex form.

.. code::

    \\α<tab>
    \\alpha


Both forward and backward completions can be deactivated by setting the
``Completer.backslash_combining_completions`` option to ``False``.

Experimental
------------

Starting with IPython 6.0, this module can make use of the Jedi library to
generate completions both using static analysis of the code, and dynamically
inspecting multiple namespaces. Jedi is an autocompletion and static analysis
for Python. The APIs attached to this new mechanism is unstable and will
raise unless use in an :any:`provisionalcompleter` context manager.

You will find that the following are experimental:

    - `provisionalcompleter`

    - `IPCompleter.completions`

    - `Completion`

    - `rectify_completions`

.. note::

    better name for `rectify_completions` ?

We welcome any feedback on these new API, and we also encourage you to try this
module in debug mode (start IPython with ``--Completer.debug=True``) in order
to have extra logging information if :any:`jedi` is crashing, or if current
IPython completer pending deprecations are returning results not yet handled
by `jedi`

Using Jedi for tab completion allow snippets like the following to work without
having to execute any code:

   >>> myvar = ['hello', 42]
   ... myvar[1].bi<tab>

Tab completion will be able to infer that ``myvar[1]`` is a real number without
executing any code unlike the previously available ``IPCompleter.greedy``
option.

Be sure to update `jedi` to the latest stable version or to try the
current development version to get better completions.

I think you can access the shell's completers through
``get_ipython().Completers()``

Debugging
---------

If `IPCompleter.debug` is `True` may return a `_FakeJediCompletion`
object containing a `str` with `jedi` debugging information attached.

"""
import builtins as builtin_mod
import glob
import inspect
import itertools
import keyword
import os
import re
import sys
import time
import warnings
from types import SimpleNamespace
from typing import Iterable, Iterator, List, Tuple

import jedi  # This is a dependency now so we don't need a try/except
import jedi.api.classes
import jedi.api.helpers
import unicodedata
from traitlets import Bool, Enum, Int, observe
from traitlets.config.configurable import Configurable

import __main__

# Just saying, after all this our file is still 1700 lines.
from IPython.core._completer import (
    _deprecation_readline_sentinel,
    _FakeJediCompletion,
    _make_signature,
    _safe_isinstance,
    back_latex_name_matches,
    back_unicode_name_matches,
    Completion,
    completions_sorting_key,
    CompletionSplitter,
    cursor_to_position,
    DELIMS,
    get__all__entries,
    GREEDY_DELIMS,
    has_open_quotes,
    match_dict_keys,
    MATCHES_LIMIT,
    position_to_cursor,
    protect_filename,
    provisionalcompleter,
)
from IPython.core.error import ProvisionalCompleterWarning, TryNext
from IPython.core.inputtransformer2 import ESC_MAGIC
from IPython.core.latex_symbols import latex_symbols
from IPython.utils import generics, PyColorize
from IPython.utils.dir2 import dir2, get_real_method
from IPython.utils.process import arg_split

# skip module doctests
skip_doctest = True

# uh i use windows so true
# jedi.settings.case_insensitive_completion = False

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

# Public API
__all__ = ["Completer", "IPCompleter"]


class Completer(Configurable):
    """

    """

    # jedi is a hard dependency
    use_jedi = Bool(
        default_value=True,
        help="Experimental: Use Jedi to generate autocompletions. "
        "Default to True if jedi is installed.",
    ).tag(config=True)

    jedi_compute_type_timeout = Int(
        default_value=400,
        help="""Experimental: restrict time (in milliseconds) during which Jedi
        can compute types.
        Set to 0 to stop computing types. Non-zero value lower than 100ms may hurt
        performance by preventing jedi to build its cache.
        """,
    ).tag(config=True)

    debug = Bool(
        default_value=False,
        help="Enable debug for the Completer. Mostly print extra "
        "information for experimental jedi integration.",
    ).tag(config=True)

    backslash_combining_completions = Bool(
        True,
        help="Enable unicode completions, e.g. \\alpha<tab> . "
        "Includes completion of latex commands, unicode names, and expanding "
        "unicode characters back to latex commands.",
    ).tag(config=True)

    def __init__(self, namespace=None, global_namespace=None, **kwargs):
        """Create a new completer for the command line.

        .. class:: Completer(namespace=ns, global_namespace=ns2)

            If unspecified, the default namespace where completions are performed
            is __main__ (technically, __main__.__dict__). Namespaces should be
            given as dictionaries.

        An optional second namespace can be given.  This allows the completer
        to handle cases where both the local and global scopes need to be
        distinguished.

        Don't bind to namespace quite yet, but flag whether the user wants a
        specific namespace or to use __main__.__dict__. This will allow us
        to bind to __main__.__dict__ at completion time, not now.
        """
        if namespace is None:
            self.use_main_ns = True
        else:
            self.use_main_ns = False
            self.namespace = namespace

        # The global namespace, if given, can be bound directly
        if global_namespace is None:
            self.global_namespace = {}
        else:
            self.global_namespace = global_namespace

        super().__init__(**kwargs)

    def complete(self, text, state):
        """Return the next possible completion for 'text'.

        This is called successively with state == 0, 1, 2, ... until it
        returns None.  The completion should begin with 'text'.
        """
        if self.use_main_ns:
            self.namespace = __main__.__dict__

        if not state:
            if "." in text:
                self.matches = self.attr_matches(text)
            else:
                self.matches = self.global_matches(text)
        try:
            return self.matches[state]
        except IndexError:
            return None

    def global_matches(self, text):
        """Compute matches when text is a simple name.

        Return a list of all keywords, built-in functions and names currently
        defined in self.namespace or self.global_namespace that match.
        """
        matches = []
        match_append = matches.append
        n = len(text)
        for lst in [
            keyword.kwlist,
            builtin_mod.__dict__.keys(),
            self.namespace.keys(),
            self.global_namespace.keys(),
        ]:
            for word in lst:
                if word[:n] == text and word != "__builtins__":
                    match_append(word)

        snake_case_re = re.compile(r"[^_]+(_[^_]+)+?\Z")
        for lst in [self.namespace.keys(), self.global_namespace.keys()]:
            shortened = {
                "_".join([sub[0] for sub in word.split("_")]): word
                for word in lst
                if snake_case_re.match(word)
            }
            for word in shortened.keys():
                if word[:n] == text and word != "__builtins__":
                    match_append(shortened[word])
        return matches

    def attr_matches(self, text):
        """Compute matches when text contains a dot.

        Assuming the text is of the form NAME.NAME....[NAME], and is
        evaluatable in self.namespace or self.global_namespace, it will be
        evaluated and its attributes (as revealed by dir()) are used as
        possible completions.  (For class instances, class members are
        also considered.)

        WARNING: this can still invoke arbitrary C code, if an object
        with a ``__getattr__`` hook is evaluated.

        """
        # Another option, seems to work great. Catches things like ''.<tab>
        m = re.match(r"(\S+([.]\w+)*)[.](\w*)$", text)

        if m:
            expr, attr = m.group(1, 3)
        elif hasattr(self, "greedy"):
            # should probably check that it has the attribute first because
            # we're deprecating this soon
            m2 = re.match(r"(.+)[.](\w*)$", self.line_buffer)
            if not m2:
                return []
            expr, attr = m2.group(1, 2)
        else:
            return []

        try:
            obj = eval(expr, self.namespace)
        except BaseException:
            try:
                obj = eval(expr, self.global_namespace)
            except BaseException:
                return []

        if self.limit_to__all__ and hasattr(obj, "__all__"):
            words = get__all__entries(obj)
        else:
            words = dir2(obj)

        try:
            words = generics.complete_object(obj, words)
        except TryNext:
            pass
        except AssertionError:
            raise
        except Exception:
            pass
        # Build match list to return
        n = len(attr)
        return ["%s.%s" % (expr, w) for w in words if w[:n] == attr]


def magic_color_matches(text: str) -> List[str]:
    """Match color schemes for %colors magic.

    Parameters
    ----------
    text :
    """
    # This used to be in oinspect at the global level but this is the only
    # place where it was invoked like that. That and oinspect itself.
    InspectColors = PyColorize.ANSICodeColors
    texts = text.split()
    if text.endswith(" "):
        # .split() strips off the trailing whitespace. Add '' back
        # so that: '%colors ' -> ['%colors', '']
        texts.append("")

    if len(texts) == 2 and (texts[0] == "colors" or texts[0] == "%colors"):
        prefix = texts[1]
        return [color for color in InspectColors.keys() if color.startswith(prefix)]


class IPCompleter(Completer):
    """Extension of the completer class with IPython-specific features.

    Attributes
    ----------
    _names
    greedy
    merge_completions

    .. todo:: The fact that the jedi settings aren't in here is a crime

    """

    greedy = Bool(default_value=False, help="Completes user input greedily.").tag(
        config=True
    )

    _names = None

    case_insensitive_completion = Bool(
        default_value=False, help="The completion is by default case insensitive"
    ).tag(config=True)

    add_bracket_after_function = Bool(
        default_value=False, help="Adds an opening bracket after a function call"
    ).tag(config=True)

    no_completion_duplicates = Bool(
        default_value=False,
        help="Don't show completions that have already been accepted",
    ).tag(config=True)

    @observe("case_insensitive_completion")
    def _case_insensitive_completion(self, change=None):
        """Need to reread the documentation on the observe function."""
        if change:
            jedi.settings.case_insensitive_completion = (
                not jedi.settings.case_insensitive_completion
            )

    @observe("greedy")
    def _greedy_changed(self, change):
        """Update the splitter and readline delims when greedy is changed."""
        if change["new"]:
            self.splitter.delims = GREEDY_DELIMS
        else:
            self.splitter.delims = DELIMS

    dict_keys_only = Bool(False, help="Whether to show dict key matches only").tag(
        config=True
    )

    merge_completions = Bool(
        True,
        help="""Whether to merge completion results into a single list

        If False, only the completion results from the first non-empty
        completer will be returned.
        """,
    ).tag(config=True)

    omit__names = Enum(
        (0, 1, 2),
        default_value=2,
        help="""Instruct the completer to omit private method names

        Specifically, when completing on ``object.<tab>``.

        When 2 [default]: all names that start with '_' will be excluded.

        When 1: all 'magic' names (``__foo__``) will be excluded.

        When 0: nothing will be excluded.
        """,
    ).tag(config=True)

    def __init__(
        self,
        shell=None,
        namespace=None,
        global_namespace=None,
        use_readline=_deprecation_readline_sentinel,
        config=None,
        **kwargs,
    ):
        """IPCompleter() -> completer

        Return a completer object.

        Parameters
        ----------
        shell : object
            a pointer to the ipython shell itself.  This is needed
            because this completer knows about magic functions, and those can
            only be accessed via the ipython instance.
        namespace : dict, optional
            an optional dict where completions are performed.
            As indicated by the signature of `Completer`, I believe that if
            this is passed as `None`, we just use ``__main__`` (specifically
            ``__main__.__dict__``).
        global_namespace : dict, optional
            secondary optional dict for completions, to
            handle cases (such as IPython embedded inside functions) where
            both Python scopes are visible.
        use_readline : bool, optional
            DEPRECATED, ignored since IPython 6.0, will have no effects
        splitter : object
            CompletionSplitter

        Methods
        -------
        _greedy_changed
            Note: Depends on `splitter` and :mod:`readline` being defined.

        """
        self.magic_escape = ESC_MAGIC
        self.splitter = CompletionSplitter()

        if use_readline is not _deprecation_readline_sentinel:
            warnings.warn(
                "The `use_readline` parameter is deprecated and ignored since IPython 6.0.",
                DeprecationWarning,
                stacklevel=2,
            )

        Completer.__init__(
            self,
            namespace=namespace,
            global_namespace=global_namespace,
            config=config,
            **kwargs,
        )

        # List where completion matches will be stored
        self.matches = []
        self.shell = shell
        # Regexp to split filenames with spaces in them
        self.space_name_re = re.compile(r"([^\\] )")
        # Hold a local ref. to glob.glob for speed
        self.glob = glob.glob

        # Determine if we are running on 'dumb' terminals, like (X)Emacs
        # buffers, to avoid completion problems.
        term = os.environ.get("TERM", "xterm")
        self.dumb_terminal = term in ["dumb", "emacs"]

        # Special handling of backslashes needed in win32 platforms
        if sys.platform == "win32":
            self.clean_glob = self._clean_glob_win32
        else:
            self.clean_glob = self._clean_glob

        # regexp to parse docstring for function signature
        self.docstring_sig_re = re.compile(r"^[\w|\s.]+[(]([^)]*)[)].*")
        self.docstring_kwd_re = re.compile(r"[\s|\[]*(\w+)(?:\s*=\s*.*)")
        # use this if positional argument name is also needed
        # = re.compile(r'[\s|\[]*(\w+)(?:\s*=?\s*.*)')

        self.magic_arg_matchers = [
            self.magic_config_matches,
            magic_color_matches,
        ]

        # This is set externally by InteractiveShell
        self.custom_completers = None

    @property
    def matchers(self):
        """All active matcher routines for completion"""
        if self.dict_keys_only:
            return [self.dict_key_matches]

        return [self.file_matches, self.magic_matches, self.dict_key_matches]
        # if self.use_jedi:
        #     return [
        #         self.file_matches,
        #         self.magic_matches,
        #         self.dict_key_matches,
        #     ]
        # else:
        #     return [
        #         self.python_matches,
        #         self.file_matches,
        #         self.magic_matches,
        #         self.python_func_kw_matches,
        #         self.dict_key_matches,
        #     ]

    def all_completions(self, text) -> List[str]:
        """Wrapper around the completions method for the benefit of emacs.

        Note
        ----
        Deleted unreachable return statement:

        return self.complete(text)[1]

        At the same scope as the 'with' statement.
        """
        prefix = text[: text.rfind(".") + 1]
        with provisionalcompleter():
            return list(
                map(lambda c: prefix + c.text, self.completions(text, len(text)))
            )

    def _clean_glob(self, text):
        return self.glob("%s*" % text)

    def _clean_glob_win32(self, text):
        return [f.replace("\\", "/") for f in self.glob("%s*" % text)]

    def file_matches(self, text):
        """Match filenames, expanding ~USER type strings.

        Most of the seemingly convoluted logic in this completer is an
        attempt to handle filenames with spaces in them.  And yet it's not
        quite perfect, because Python's readline doesn't expose all of the
        GNU readline details needed for this to be done correctly.

        For a filename with a space in it, the printed completions will be
        only the parts after what's already been typed (instead of the
        full completions, as is normally done).  I don't think with the
        current (as of Python 2.3) Python readline it's possible to do
        better.

        Note
        ----
        Leading :kbd:`!` are stripped.

        """
        if text.startswith("!"):
            text = text[1:]
            text_prefix = "!"
        else:
            text_prefix = ""

        text_until_cursor = self.text_until_cursor
        # track strings with open quotes
        open_quotes = has_open_quotes(text_until_cursor)

        if "(" in text_until_cursor or "[" in text_until_cursor:
            lsplit = text
        else:
            try:
                # arg_split ~ shlex.split, but with unicode bugs fixed by us
                lsplit = arg_split(text_until_cursor)[-1]
            except ValueError:
                # typically an unmatched ", or backslash without escaped char.
                if open_quotes:
                    lsplit = text_until_cursor.split(open_quotes)[-1]
                else:
                    return []
            except IndexError:
                # tab pressed on empty line
                lsplit = ""

        if not open_quotes and lsplit != protect_filename(lsplit):
            # if protectables are found, do matching on the whole escaped name
            has_protectables = True
            text0, text = text, lsplit
        else:
            has_protectables = False
            text = os.path.expanduser(text)

        if text == "":
            return [text_prefix + protect_filename(f) for f in self.glob("*")]

        # Compute the matches from the filesystem
        if sys.platform == "win32":
            m0 = self.clean_glob(text)
        else:
            m0 = self.clean_glob(text.replace("\\", ""))

        if has_protectables:
            # If we had protectables, we need to revert our changes to the
            # beginning of filename so that we don't double-write the part
            # of the filename we have so far
            len_lsplit = len(lsplit)
            matches = [
                text_prefix + text0 + protect_filename(f[len_lsplit:]) for f in m0
            ]
        else:
            if open_quotes:
                # if we have a string with an open quote, we don't need to
                # protect the names beyond the quote (and we _shouldn't_, as
                # it would cause bugs when the filesystem call is made).
                matches = (
                    m0
                    if sys.platform == "win32"
                    else [protect_filename(f, open_quotes) for f in m0]
                )
            else:
                matches = [text_prefix + protect_filename(f) for f in m0]

        # Mark directories in input list by appending '/' to their names.
        return [x + "/" if os.path.isdir(x) else x for x in matches]

    def magic_matches(self, text):
        """Match magics.

        Completion logic:

        - user gives %%: only do cell magics
        - user gives %: do both line and cell magics
        - no prefix: do both

        In other words, line magics are skipped if the user gives %% explicitly.
        We also exclude magics that match any currently visible names.

        See Also
        --------
        https://github.com/ipython/ipython/issues/4877
            However, with no prefix we consolidate `%lsmagic` and get everything.

        https://github.com/ipython/ipython/issues/10754
            Unless the user has typed a :kbd:`%`:

        Parameters
        ----------
        text

        Returns
        -------
        object

        """
        # Get all shell magics now rather than statically, so magics loaded at
        # runtime show up too.
        lsm = self.shell.magics_manager.lsmagic()
        line_magics = lsm["line"]
        cell_magics = lsm["cell"]
        pre = self.magic_escape
        pre2 = pre + pre

        explicit_magic = text.startswith(pre)

        bare_text = text.lstrip(pre)
        global_matches = self.global_matches(bare_text)
        if not explicit_magic:

            def matches(magic):
                """
                Filter magics, in particular remove magics that match
                a name present in global namespace.
                """
                return magic.startswith(bare_text) and magic not in global_matches

        else:

            def matches(magic):
                return magic.startswith(bare_text)

        comp = [pre2 + m for m in cell_magics if matches(m)]
        if not text.startswith(pre2):
            comp += [pre + m for m in line_magics if matches(m)]

        return comp

    def magic_config_matches(self, text: str) -> List[str]:
        """ Match class names and attributes for %config magic """
        texts = text.strip().split()

        if len(texts) > 0 and (texts[0] == "config" or texts[0] == "%config"):
            # get all configuration classes
            classes = sorted(
                set(
                    [
                        c
                        for c in self.shell.configurables
                        if c.__class__.class_traits(config=True)
                    ]
                ),
                key=lambda x: x.__class__.__name__,
            )
            classnames = [c.__class__.__name__ for c in classes]

            # return all classnames if config or %config is given
            if len(texts) == 1:
                return classnames

            # match classname
            classname_texts = texts[1].split(".")
            classname = classname_texts[0]
            classname_matches = [c for c in classnames if c.startswith(classname)]

            # return matched classes or the matched class with attributes
            if texts[1].find(".") < 0:
                return classname_matches
            elif len(classname_matches) == 1 and classname_matches[0] == classname:
                cls = classes[classnames.index(classname)].__class__
                help = cls.class_get_help()
                # strip leading '--' from cl-args:
                help = re.sub(re.compile(r"^--", re.MULTILINE), "", help)
                return [
                    attr.split("=")[0]
                    for attr in help.strip().splitlines()
                    if attr.startswith(texts[1])
                ]
        return []

    def _jedi_matches(self, cursor_column: int, cursor_line: int, text: str):
        """Generate completions using jedi.

        Parameters
        ----------
        cursor_column : int
            column position of the cursor in ``text``, 0-indexed.
        cursor_line : int
            line position of the cursor in ``text``, 0-indexed
        text : str
            text to complete

        Returns
        -------
        Anonymous list of `jedi.api.Completions` objects.
            Return a list of `jedi.api.Completions` object from a ``text`` and
            cursor position.

        Notes
        -----
        This method initializes the `jedi.api.Interpreter` object, has 4
        closures/lambda completion filters and silently catches as many errors
        as we can unless our 'debug' parameter is `True`.

        Woof.

        """
        namespaces = [self.namespace]
        if self.global_namespace is not None:
            namespaces.append(self.global_namespace)

        def completion_filter(x):
            return x

        offset = cursor_to_position(text, cursor_line, cursor_column)
        # filter output if we are completing for object members
        if offset:
            pre = text[offset - 1]
            if pre == ".":
                if self.omit__names == 2:

                    def completion_filter(c):
                        return not c.name.startswith("_")

                elif self.omit__names == 1:

                    def completion_filter(c):
                        return not (c.name.startswith("__") and c.name.endswith("__"))

                elif not self.omit__names:

                    def completion_filter(x):
                        return x

                else:
                    raise ValueError(
                        "Don't understand self.omit__names == {}".format(
                            self.omit__names
                        )
                    )

        interpreter = jedi.Interpreter(
            text[:offset], namespaces, column=cursor_column, line=cursor_line + 1
        )
        try_jedi = True

        try:
            # should we check the type of the node is Error ?
            try:
                # jedi < 0.11
                from jedi.parser.tree import ErrorLeaf
            except ImportError:
                # jedi >= 0.11
                from parso.tree import ErrorLeaf

            next_to_last_tree = interpreter._get_module().tree_node.children[-2]
            completing_string = False
            if isinstance(next_to_last_tree, ErrorLeaf):
                completing_string = next_to_last_tree.value.lstrip()[0] in {'"', "'"}
            # if we are in a string jedi is likely not the right candidate for
            # now. Skip it.
            try_jedi = not completing_string
        except Exception as e:
            if self.debug:
                print("Error detecting if completing a non-finished string :", e, "|")

        if not try_jedi:
            return []
        try:
            return filter(completion_filter, interpreter.completions())
        except Exception as e:
            if self.debug:
                return [
                    _FakeJediCompletion(
                        'Oops Jedi has crashed, please report a bug with the following:\n"""\n%s\ns"""'
                        % e
                    )
                ]
            else:
                return []

    def python_matches(self, text):
        """Match attributes or global python names."""
        if "." in text:
            try:
                matches = self.attr_matches(text)
                if text.endswith(".") and self.omit__names:
                    if self.omit__names == 1:
                        # true if txt is _not_ a __ name, false otherwise:
                        def no__name(txt):
                            return re.match(r".*[.]__.*?__", txt) is None

                    else:
                        # true if txt is _not_ a _ name, false otherwise:
                        no__name = (
                            lambda txt: re.match(r"[.]_.*?", txt[txt.rindex(".") :])
                            is None
                        )
                    matches = filter(no__name, matches)
            except NameError:
                # catches <undefined attributes>.<tab>
                matches = []
        else:
            matches = self.global_matches(text)
        return matches

    def _default_arguments_from_docstring(self, doc=None):
        """Parse the first line of docstring for call signature.

        Docstring should be of the form:

        .. function:: min(iterable[, key=func])

        It can also parse cython docstring of the form:

        .. function:: Minuit.migrad(self, int ncall=10000, resume=True, int nsplit=1)

        Parameters
        ----------
        doc now optional

        """
        if doc is None:
            return []

        # care only the firstline
        line = doc.lstrip().splitlines()[0]

        # p = re.compile(r'^[\w|\s.]+\(([^)]*)\).*')
        # 'min(iterable[, key=func])\n' -> 'iterable[, key=func]'
        sig = self.docstring_sig_re.search(line)
        if sig is None:
            return []
        # iterable[, key=func]' -> ['iterable[' ,' key=func]']
        sig = sig.groups()[0].split(",")
        ret = []
        for s in sig:
            # re.compile(r'[\s|\[]*(\w+)(?:\s*=\s*.*)')
            ret += self.docstring_kwd_re.findall(s)
        return ret

    def _default_arguments(self, obj):
        """Return the list of default arguments of obj if it is callable,
        or empty list otherwise.

        Parameters
        ----------
        obj :
        """
        call_obj = obj
        ret = []
        if inspect.isbuiltin(obj):
            pass
        elif not (inspect.isfunction(obj) or inspect.ismethod(obj)):
            if inspect.isclass(obj):
                # for cython embedsignature=True the constructor docstring
                # belongs to the object itself not __init__
                ret += self._default_arguments_from_docstring(
                    getattr(obj, "__doc__", "")
                )
                # for classes, check for __init__,__new__
                call_obj = getattr(obj, "__init__", None) or getattr(
                    obj, "__new__", None
                )
            # for all others, check if they are __call__able
            elif hasattr(obj, "__call__"):
                call_obj = obj.__call__
        ret += self._default_arguments_from_docstring(getattr(call_obj, "__doc__", ""))

        _keeps = (
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )

        try:
            sig = inspect.signature(call_obj)
            ret.extend(k for k, v in sig.parameters.items() if v.kind in _keeps)
        except ValueError:
            pass

        return list(set(ret))

    def python_func_kw_matches(self, text):
        """Match named parameters (kwargs) of the last open function.

        1. find the nearest identifier that comes before an unclosed
           parenthesis before the cursor
           e.g. for "foo (1+bar(x), pa<cursor>,a=1)", the candidate is "foo"

           - Oddly though we match tokens against their literal string representations.
             Would it prove easier to tokenize inputs?

        2. Concatenate dotted names ("foo.bar" for "foo.bar(x, pa" )

        3. Find all named arguments already assigned to, as to avoid suggesting
           them again

        Returns
        -------
        argmatches : set
            The set of possible completions, 'namedArgs', reduced by the
            named arguments already displayed, 'usedNamedArgs',
            as determined in Step 3.

        """

        if "." in text:  # a parameter cannot be dotted
            return []
        try:
            regexp = self.__funcParamsRegex
        except AttributeError:
            regexp = self.__funcParamsRegex = re.compile(
                r"""
                '.*?(?<!\\)' |    # single quoted strings or
                ".*?(?<!\\)" |    # double quoted strings or
                \w+          |    # identifier
                \S                # other characters
                """,
                re.VERBOSE | re.DOTALL,
            )
        tokens = regexp.findall(self.text_until_cursor)
        iterTokens = reversed(tokens)
        openPar = 0

        for token in iterTokens:
            if token == ")":
                openPar -= 1
            elif token == "(":
                openPar += 1
                if openPar > 0:
                    # found the last unclosed parenthesis
                    break
        else:
            return []
        ids = []
        isId = re.compile(r"\w+$").match

        while True:
            try:
                ids.append(next(iterTokens))
                if not isId(ids[-1]):
                    ids.pop()
                    break
                if not next(iterTokens) == ".":
                    break
            except StopIteration:
                break

        usedNamedArgs = set()
        par_level = -1
        for token, next_token in zip(tokens, tokens[1:]):
            if token == "(":
                par_level += 1
            elif token == ")":
                par_level -= 1

            if par_level:
                continue

            if next_token != "=":
                continue

            usedNamedArgs.add(token)

        argMatches = []
        try:
            callableObj = ".".join(ids[::-1])
            namedArgs = self._default_arguments(eval(callableObj, self.namespace))

            # Remove used named arguments from the list, no need to show twice
            for namedArg in set(namedArgs) - usedNamedArgs:
                if namedArg.startswith(text):
                    argMatches.append("%s=" % namedArg)
        except BaseException:
            pass

        return argMatches

    def dict_key_matches(self, text):
        """Match string keys in a dictionary, after e.g. 'foo['."""

        def get_keys(obj):
            """Objects can define their own completions.

            This can be done by defining an _ipy_key_completions_() method.

            **Wait where in the docs is this mentioned????**

            Returns
            -------
            object

            """
            method = get_real_method(obj, "_ipython_key_completions_")
            if method is not None:
                return method()

            # Special case some common in-memory dict-like types
            if isinstance(obj, dict) or _safe_isinstance(obj, "pandas", "DataFrame"):
                try:
                    return list(obj.keys())
                except Exception:
                    return []
            elif _safe_isinstance(obj, "numpy", "ndarray") or _safe_isinstance(
                obj, "numpy", "void"
            ):
                return obj.dtype.names or []
            return []

        try:
            regexps = self.__dict_key_regexps
        except AttributeError:
            dict_key_re_fmt = r"""(?x)
            (  # match dict-referring expression wrt greedy setting
                %s
            )
            \[   # open bracket
            \s*  # and optional whitespace
            ([uUbB]?  # string prefix (r not handled)
                (?:   # unclosed string
                    '(?:[^']|(?<!\\)\\')*
                |
                    "(?:[^"]|(?<!\\)\\")*
                )
            )?
            $
            """
            regexps = self.__dict_key_regexps = {
                False: re.compile(
                    dict_key_re_fmt
                    % r"""
                                  # identifiers separated by .
                                  (?!\d)\w+
                                  (?:\.(?!\d)\w+)*
                                  """
                ),
                True: re.compile(dict_key_re_fmt % """.+"""),
            }

        match = regexps[self.greedy].search(self.text_until_cursor)
        if match is None:
            return []

        expr, prefix = match.groups()
        try:
            obj = eval(expr, self.namespace)
        except Exception:
            try:
                obj = eval(expr, self.global_namespace)
            except Exception:
                return []

        keys = get_keys(obj)
        if not keys:
            return keys
        closing_quote, token_offset, matches = match_dict_keys(
            keys, prefix, self.splitter.delims
        )
        if not matches:
            return matches

        # get the cursor position of
        # - the text being completed
        # - the start of the key text
        # - the start of the completion
        text_start = len(self.text_until_cursor) - len(text)
        if prefix:
            key_start = match.start(2)
            completion_start = key_start + token_offset
        else:
            key_start = completion_start = match.end()

        # grab the leading prefix, to make sure all completions start with
        # `text`
        if text_start > key_start:
            leading = ""
        else:
            leading = text[text_start:completion_start]

        # the index of the `[` character
        bracket_idx = match.end(1)

        # append closing quote and bracket as appropriate
        # this is *not* appropriate if the opening quote or bracket is outside
        # the text given to this method
        suf = ""
        continuation = self.line_buffer[len(self.text_until_cursor) :]
        if key_start > text_start and closing_quote:
            # quotes were opened inside text, maybe close them
            if continuation.startswith(closing_quote):
                continuation = continuation[len(closing_quote) :]
            else:
                suf += closing_quote
        if bracket_idx > text_start:
            # brackets were opened inside text, maybe close them
            if not continuation.startswith("]"):
                suf += "]"

        return [leading + k + suf for k in matches]

    def unicode_name_matches(self, text):
        r"""Match Latex-like syntax for unicode characters base
        on the name of the character.

        This does  ``\\GREEK SMALL LETTER ETA`` -> ``η``

        Works only on valid python 3 identifier, or on combining characters that
        will combine to form a valid identifier.

        .. note:: Utilizes external mod unicodedata.

        Parameters
        ----------
        text :

        """
        slashpos = text.rfind("\\")
        if slashpos > -1:
            s = text[slashpos + 1 :]
            try:
                unic = unicodedata.lookup(s)
                # allow combining chars
                if ("a" + unic).isidentifier():
                    return "\\" + s, [unic]
            except KeyError:
                pass
        return "", []

    def latex_matches(self, text):
        r"""Match Latex syntax for unicode characters.

        This does both ``\\alp`` -> ``\\alpha`` and ``\\alpha`` -> ``α``

        Used on Python 3 only.

        Parameters
        ----------
        text :

        """
        slashpos = text.rfind("\\")
        if slashpos > -1:
            s = text[slashpos:]
            if s in latex_symbols:
                # Try to complete a full latex symbol to unicode
                # \\alpha -> α
                return s, [latex_symbols[s]]
            else:
                # If a user has partially typed a latex symbol, give them
                # a full list of options \al -> [\aleph, \alpha]
                matches = [k for k in latex_symbols if k.startswith(s)]
                return s, matches
        return "", []

    def dispatch_custom_completer(self, text):
        """Create a little structure to pass relevant information to a completer.

        Parameters
        ----------
        text :

        Returns
        -------
        object
        """
        if not self.custom_completers:
            return

        line = self.line_buffer
        if not line.strip():
            return None

        event = SimpleNamespace()
        event.line = line
        event.symbol = text
        cmd = line.split(None, 1)[0]
        event.command = cmd
        event.text_until_cursor = self.text_until_cursor

        # for foo etc, try also to find completer for %foo
        if not cmd.startswith(self.magic_escape):
            try_magic = self.custom_completers.s_matches(self.magic_escape + cmd)
        else:
            try_magic = []

        for c in itertools.chain(
            self.custom_completers.s_matches(cmd),
            try_magic,
            self.custom_completers.flat_matches(self.text_until_cursor),
        ):
            try:
                res = c(event)
                if res:
                    # first, try case sensitive match
                    withcase = [r for r in res if r.startswith(text)]
                    if withcase:
                        return withcase
                    # if none, then case insensitive ones are ok too
                    text_low = text.lower()
                    return [r for r in res if r.lower().startswith(text_low)]
            except TryNext:
                pass
            except KeyboardInterrupt:
                """
                If custom completer take too long,
                let keyboard interrupt abort and return nothing.
                """
                break

        return None

    def completions(self, text: str, offset: int) -> Iterator[Completion]:
        """Returns an iterator over the possible completions.

        .. warning:: Unstable

            This function is unstable, API may change without warning.
            It will also raise unless use in proper context manager.

        Parameters
        ----------
        text:str
            Full text of the current input, multi line string.
        offset:int
            Integer representing the position of the cursor in ``text``. Offset
            is 0-based indexed.

        Yields
        ------
        :any:`Completion` object

        The cursor on a text can either be seen as being "in between"
        characters or "On" a character depending on the interface visible to
        the user. For consistency the cursor being on "in between" characters X
        and Y is equivalent to the cursor being "on" character Y, that is to say
        the character the cursor is on is considered as being after the cursor.

        Combining characters may span more that one position in the
        text.

        .. note::

            If 'debug' is `True` will yield a ``--jedi/ipython--``
            fake Completion token to distinguish completion returned by Jedi
            and usual IPython completion.

        .. note::

            Completions are not completely deduplicated yet. If identical
            completions are coming from different sources this function does not
            ensure that each completion object will only be present once.

        """
        warnings.warn(
            "_complete is a provisional API (as of IPython 6.0). "
            "It may change without warnings. "
            "Use in corresponding context manager.",
            category=ProvisionalCompleterWarning,
            stacklevel=2,
        )

        seen = set()
        try:
            for c in self._completions(
                text, offset, _timeout=self.jedi_compute_type_timeout / 1000
            ):
                if c and (c in seen):
                    continue
                yield c
                seen.add(c)
        except KeyboardInterrupt:
            """if completions take too long and users send keyboard interrupt,
            do not crash and return ASAP. """
            pass

    def _completions(
        self, full_text: str, offset: int, *, _timeout
    ) -> Iterator[Completion]:
        """Core completion function.

        Same signature as :any:`completions`, with the extra 'timeout'
        parameter (in seconds).

        Computing `jedi` completion ``.type`` can be quite expensive (it is a
        lazy property) and can require some warm-up, more warm up than just
        computing the ``name`` of a completion. The warm-up can be from:

            - The first time a module is encountered after
              install/update. In which case:

                - actually build parse/inference tree.

            - First time the module is encountered in a session:

                - load tree from disk.

        We don't want to block completions for tens of seconds so we give the
        completer a budget of ``_timeout`` seconds per invocation to compute
        completions types.

        The completions that have not yet been computed will
        be marked as "unknown", and will have a chance to be computed next
        round when things get cached.

        .. tip::
            Keep in mind that Jedi is not the only thing calculating
            the completion so keep the timeout short-ish as if we take more
            than, for instance, 0.3 seconds, we still have a lot more
            processing to do.

        .. todo:: This method could probably be hugely enhanced by some comprehensions.

        """
        deadline = time.monotonic() + _timeout

        before = full_text[:offset]
        cursor_line, cursor_column = position_to_cursor(full_text, offset)

        matched_text, matches, matches_origin, jedi_matches = self._complete(
            full_text=full_text, cursor_line=cursor_line, cursor_pos=cursor_column
        )

        iter_jm = iter(jedi_matches)
        if _timeout:
            for jm in iter_jm:
                try:
                    type_ = jm.type
                except Exception:
                    if self.debug:
                        print("Error in Jedi getting type of ", jm)
                    type_ = None
                delta = len(jm.name_with_symbols) - len(jm.complete)
                if type_ == "function":
                    signature = _make_signature(jm)
                else:
                    signature = ""
                yield Completion(
                    start=offset - delta,
                    end=offset,
                    text=jm.name_with_symbols,
                    type=type_,
                    signature=signature,
                    _origin="jedi",
                )

                if time.monotonic() > deadline:
                    break

        for jm in iter_jm:
            delta = len(jm.name_with_symbols) - len(jm.complete)
            yield Completion(
                start=offset - delta,
                end=offset,
                text=jm.name_with_symbols,
                type="<unknown>",  # don't compute type for speed
                _origin="jedi",
                signature="",
            )

        start_offset = before.rfind(matched_text)

        # TODO:
        # Suppress this, right now just for debug.
        if jedi_matches and matches and self.debug:
            yield Completion(
                start=start_offset,
                end=offset,
                text="--jedi/ipython--",
                _origin="debug",
                type="none",
                signature="",
            )

        # I'm unsure if this is always true, so let's assert and see if it
        # crash
        # ....Are you serious?
        assert before.endswith(matched_text)
        for m, t in zip(matches, matches_origin):
            yield Completion(
                start=start_offset,
                end=offset,
                text=m,
                _origin=t,
                signature="",
                type="<unknown>",
            )

    def complete(self, text=None, line_buffer=None, cursor_pos=None):
        """Find completions for the given text and line context.

        Note that both the text and the line_buffer are optional, but at least
        one of them must be given.

        Parameters
        ----------
          text : string, optional
            Text to perform the completion on.  If not given, the line buffer
            is split using the instance's CompletionSplitter object.

          line_buffer : string, optional
            If not given, the completer attempts to obtain the current line
            buffer via readline.  This keyword allows clients which are
            requesting for text completions in non-readline contexts to inform
            the completer of the entire text.

          cursor_pos : int, optional
            Index of the cursor in the full line buffer.  Should be provided by
            remote frontends where kernel has no access to frontend state.

        Returns
        -------
        text : str
          Text that was actually used in the completion.

        matches : list
          A list of completion matches.


        .. note::

            This API is likely to be deprecated and replaced by
            `IPCompleter.completions` in the future.


        """
        warnings.warn(
            "`Completer.complete` is pending deprecation since "
            "IPython 6.0 and will be replaced by `Completer.completions`.",
            PendingDeprecationWarning,
        )
        # potential todo, FOLD the 3rd throw away argument of _complete
        # into the first 2 one.
        return self._complete(
            line_buffer=line_buffer, cursor_pos=cursor_pos, text=text, cursor_line=0
        )[:2]

    def _complete(
        self, *, cursor_line, cursor_pos, line_buffer=None, text=None, full_text=None
    ) -> Tuple[str, List[str], List[str], Iterable[_FakeJediCompletion]]:
        """
        Like complete but can also returns raw jedi completions as well as the
        origin of the completion text. This could (and should) be made much
        cleaner but that will be simpler once we drop the old (and stateful)
        :any:`complete` API.

        With current provisional API, cursor_pos act both (depending on the
        caller) as the offset in the ``text`` or ``line_buffer``, or as the
        ``column`` when passing multiline strings.

        This could/should be renamed but would add extra noise.

        But no matter what this should be refactored this one method
        undertakes a large number of different tasks.

        Parameters
        ----------
        cursor_pos :
            If the cursor position isn't given, the only sane assumption we can
            make is that it's at the end of the line (the common case).
        text :
            If text is either None or an empty string, rely on the line buffer.
        """
        if cursor_pos is None:
            cursor_pos = len(line_buffer) if text is None else len(text)
            # uh wouldn't that just be this?
            # cursor_pos = len(line_buffer)

        if self.use_main_ns:
            self.namespace = __main__.__dict__

        if (not line_buffer) and full_text:
            line_buffer = full_text.split("\n")[cursor_line]

        if not text:
            text = self.splitter.split_line(line_buffer, cursor_pos)

        if self.backslash_combining_completions:
            # allow deactivation of these on windows.
            # Or just anyone that doesn't have this activated. This entire block
            # of logic would be easier to follow as a separate method.
            base_text = text if not line_buffer else line_buffer[:cursor_pos]
            latex_text, latex_matches = self.latex_matches(base_text)
            if latex_matches:
                return (
                    latex_text,
                    latex_matches,
                    ["latex_matches"] * len(latex_matches),
                    (),
                )
            for meth in (
                self.unicode_name_matches,
                back_latex_name_matches,
                back_unicode_name_matches,
                self.fwd_unicode_match,
            ):
                name_text, name_matches = meth(base_text)
                if name_text:
                    return (
                        name_text,
                        name_matches[:MATCHES_LIMIT],
                        [meth.__qualname__] * min(len(name_matches), MATCHES_LIMIT),
                        (),
                    )

        # If no line buffer is given, assume the input text is all there was
        if line_buffer is None:
            line_buffer = text

        self.line_buffer = line_buffer
        self.text_until_cursor = self.line_buffer[:cursor_pos]

        # Do magic arg matches
        for matcher in self.magic_arg_matchers:
            matches = list(matcher(line_buffer))[:MATCHES_LIMIT]
            if matches:
                origins = [matcher.__qualname__] * len(matches)
                return text, matches, origins, ()

        # Start with a clean slate of completions
        matches = []

        # FIXME: we should extend our api to return a dict with completions for
        # different types of objects.  The rlcomplete() method could then
        # simply collapse the dict into a list for readline, but we'd have
        # richer completion semantics in other environments.
        completions = ()
        if self.use_jedi:
            if not full_text:
                full_text = line_buffer
            completions = self._jedi_matches(cursor_pos, cursor_line, full_text)

            if self.merge_completions:
                matches = []
                for matcher in self.matchers:
                    try:
                        matches.extend(
                            [(m, matcher.__qualname__) for m in matcher(text)]
                        )
                    except:
                        # Show the ugly traceback if the matcher causes an
                        # exception, but do NOT crash the kernel!
                        # ooo we should start doing this more frequently. maybe
                        # make this a method of interactiveapp because we do
                        # sloppier versions of this everywhere
                        sys.excepthook(*sys.exc_info())
            else:
                for matcher in self.matchers:
                    matches = [(m, matcher.__qualname__) for m in matcher(text)]
                    if matches:
                        break

        seen = set()
        filtered_matches = set()
        for m in matches:
            t, c = m
            if t not in seen:
                filtered_matches.add(m)
                seen.add(t)

        _filtered_matches = sorted(
            filtered_matches, key=lambda x: completions_sorting_key(x[0])
        )

        custom_res = [(m, "custom") for m in self.dispatch_custom_completer(text) or []]

        _filtered_matches = custom_res or _filtered_matches

        _filtered_matches = _filtered_matches[:MATCHES_LIMIT]
        _matches = [m[0] for m in _filtered_matches]
        origins = [m[1] for m in _filtered_matches]

        self.matches = _matches

        return text, _matches, origins, completions

    def fwd_unicode_match(self, text: str) -> Tuple[str, list]:
        """

        Parameters
        ----------
        text :

        Returns
        -------

        """
        if self._names is None:
            self._names = []
            for c in range(0, 0x10FFFF + 1):
                try:
                    self._names.append(unicodedata.name(chr(c)))
                except ValueError:
                    pass

        slashpos = text.rfind("\\")
        # if text starts with slash
        if slashpos > -1:
            s = text[slashpos + 1 :]
            candidates = [x for x in self._names if x.startswith(s)]
            if candidates:
                return s, candidates
            else:
                return "", ()

        # if text does not start with slash
        else:
            return "", ()
