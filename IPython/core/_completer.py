"""completer has 700 lines that can't be imported because they're not in __all__.

It's also really hard to read from how huge the file is. I'm moving everything
into this "hidden" module.
"""
import os
import re
import string
import sys
import unicodedata
import warnings
from contextlib import contextmanager
from importlib import import_module
from typing import Iterable, Iterator, List, Tuple

from traitlets import Bool

from IPython.core.error import ProvisionalCompleterWarning
from IPython.core.latex_symbols import reverse_latex_symbol

if sys.platform == "win32":
    PROTECTABLES = " "
else:
    PROTECTABLES = " ()[]{}?=\\|;:'#*\"^&"

# Protect against returning an enormous number of completions which the
# frontend may have trouble processing.
# not all of my devices can handle 500. can we not put these settings in a
# configurable?
MATCHES_LIMIT = 50

_deprecation_readline_sentinel = object()

warnings.filterwarnings("error", category=ProvisionalCompleterWarning)


@contextmanager
def provisionalcompleter(action="ignore"):
    """Context manager for unstable API features.

    This context manager has to be used in any place where unstable completer
    behavior and API may be called.::

        with provisionalcompleter():
            completer.do_experimetal_things() # works

        completer.do_experimental_things() # raises.

    .. note:: Unstable

        By using this context manager you agree that the API in use may change
        without warning, and that you won't complain if they do so.
        We'll be happy to get your feedback, and review any
        feature requests or improvements on any of the unstable APIs !

    .. warning:: Doesn't this drop any args passed to the function it wraps?

        Or does contextlib.context_manager handle that for us?
        I'm surprised to see no args or kwargs here.

    """
    with warnings.catch_warnings():
        warnings.filterwarnings(action, category=ProvisionalCompleterWarning)
        yield


def has_open_quotes(s):
    """Return whether a string has open quotes.

    This simply counts whether the number of quote characters of either type in
    the string is odd.

    We check " first, then ', so complex cases with nested quotes will get
    the " to take precedence.

    Parameters
    ----------
    s : str
        String to check

    Returns
    -------
    str or bool
       If there is an open quote, the quote character is returned.
       Else, return False.

    """
    if s.count('"') % 2:
        return '"'
    elif s.count("'") % 2:
        return "'"
    else:
        return False


def protect_filename(s, protectables=PROTECTABLES):
    """Escape a string to protect certain characters.

    Parameters
    -----------
    s : str
        String to escape
    protectables : str
        Symbols to escape on Windows.

    """
    if set(s) & set(protectables):
        if sys.platform == "win32":
            return '"' + s + '"'
        else:
            return "".join(("\\" + c if c in protectables else c) for c in s)
    else:
        return s


def expand_user(path: str) -> Tuple[str, bool, str]:
    """Expand :kbd:`~` style usernames in strings.

    This is similar to :func:`os.path.expanduser`, but it computes and returns
    extra information that will be useful if the input was being used in
    computing completions, and you wish to return the completions with the
    original :kbd:`~` instead of its expanded value.

    ....Isn't this also similar to IPython.utils.path.expand_path?

    Parameters
    ----------
    path : str
        String to be expanded.  If no ~ is present, the output is the same as the
        input.

    Returns
    -------
    newpath : str
        Result of ~ expansion in the input path.
    tilde_expand : bool
        Whether any expansion was performed or not.
    tilde_val : str
        The value that ~ was replaced with.

    """
    # Default values
    tilde_expand = False
    tilde_val = ""
    newpath = path

    if path.startswith("~"):
        tilde_expand = True
        rest = len(path) - 1
        newpath = os.path.expanduser(path)
        if rest:
            tilde_val = newpath[:-rest]
        else:
            tilde_val = newpath

    return newpath, tilde_expand, tilde_val


def compress_user(path: str, tilde_expand: bool, tilde_val: str) -> str:
    """Does the opposite of expand_user, with its outputs."""
    if tilde_expand:
        return path.replace(tilde_val, "~")
    else:
        return path


def completions_sorting_key(word):
    """Key for sorting completions.

    This does several things:

    - Demote any completions starting with underscores to the end

    - Insert any %magic and %%cellmagic completions in the alphabetical order
      by their name
    """
    prio1, prio2 = 0, 0

    if word.startswith("__"):
        prio1 = 2
    elif word.startswith("_"):
        prio1 = 1

    if word.endswith("="):
        prio1 = -1

    if word.startswith("%%"):
        # If there's another % in there, this is something else, so leave it
        # alone
        if "%" not in word[2:]:
            word = word[2:]
            prio2 = 2
    elif word.startswith("%"):
        if "%" not in word[1:]:
            word = word[1:]
            prio2 = 1

    return prio1, word, prio2


class _FakeJediCompletion:
    """
    This is a workaround to communicate to the UI that Jedi has crashed and to
    report a bug. Will be used only if :any:`IPCompleter.debug` is set to True.

    Added in IPython 6.0 so should likely be removed for 7.0

    .. todo:: Uhh.

    """

    def __init__(self, name):
        self.name = name
        self.complete = name
        self.type = "crashed"
        self.name_with_symbols = name
        self.signature = ""
        self._origin = "fake"

    def __repr__(self):
        return "{}".format(
            self.__class__.__name__, "<Fake completion object jedi has crashed>"
        )


class Completion:
    """Completion object used and return by IPython completers.

    .. warning:: Unstable

        This function is unstable, API may change without warning.
        It will also raise unless use in proper context manager.

    This act as a middle ground :any:`Completion` object between the
    :any:`jedi.api.classes.Completion` object and the Prompt Toolkit completion
    object. While Jedi need a lot of information about evaluator and how the
    code should be ran/inspected, PromptToolkit (and other frontend) mostly
    need user facing information.

    - Which range should be replaced replaced by what.
    - Some metadata (like completion type), or meta information to displayed to
      the use user.

    For debugging purpose we can also store the origin of the completion (``jedi``,
    ``IPython.python_matches``, ``IPython.magics_matches``...).
    """

    __slots__ = ["start", "end", "text", "type", "signature", "_origin"]

    def __init__(
        self,
        start: int,
        end: int,
        text: str,
        *,
        type: str = None,
        _origin="",
        signature="",
    ) -> None:
        """

        Returns
        -------
        object
        """
        warnings.warn(
            "``Completion`` is a provisional API (as of IPython 6.0). "
            "It may change without warnings. "
            "Use in corresponding context manager.",
            category=ProvisionalCompleterWarning,
            stacklevel=2,
        )

        self.start = start
        self.end = end
        self.text = text
        self.type = type
        self.signature = signature
        self._origin = _origin

    def __repr__(self):
        return "<Completion start=%s end=%s text=%r type=%r, signature=%r,>" % (
            self.start,
            self.end,
            self.text,
            self.type or "?",
            self.signature or "?",
        )

    def __eq__(self, other) -> Bool:
        """
        Equality and hash do not hash the type (as some completer may not be
        able to infer the type), but are use to (partially) de-duplicate
        completion.

        Completely de-duplicating completion is a bit tricker that just
        comparing as it depends on surrounding text, which Completions are not
        aware of.
        """
        return (
            self.start == other.start
            and self.end == other.end
            and self.text == other.text
        )

    def __hash__(self):
        return hash((self.start, self.end, self.text))


_IC = Iterable[Completion]


def _deduplicate_completions(text: str, completions: _IC) -> _IC:
    """
    Deduplicate a set of completions.

    .. warning:: Unstable

        This function is unstable, API may change without warning.

    Parameters
    ----------
    text: str
        text that should be completed.
    completions: Iterator[Completion]
        iterator over the completions to deduplicate

    Yields
    ------
    `Completions` objects


    Completions coming from multiple sources, may be different but end up having
    the same effect when applied to ``text``. If this is the case, this will
    consider completions as equal and only emit the first encountered.

    Not folded in `completions()` yet for debugging purpose, and to detect when
    the IPython completer does return things that Jedi does not, but should be
    at some point.
    """
    completions = list(completions)
    if not completions:
        return

    new_start = min(c.start for c in completions)
    new_end = max(c.end for c in completions)

    seen = set()
    for c in completions:
        new_text = text[new_start : c.start] + c.text + text[c.end : new_end]
        if new_text not in seen:
            yield c
            seen.add(new_text)


def rectify_completions(text: str, completions: _IC, *, _debug=False) -> _IC:
    """
    Rectify a set of completions to all have the same ``start`` and ``end``

    .. warning:: Unstable

        This function is unstable, API may change without warning.
        It will also raise unless use in proper context manager.

    Parameters
    ----------
    _debug :
    text: str
        text that should be completed.
    completions: Iterator[Completion]
        iterator over the completions to rectify


    :any:`jedi.api.classes.Completion` s returned by Jedi may not have the same start and end, though
    the Jupyter Protocol requires them to behave like so. This will readjust
    the completion to have the same ``start`` and ``end`` by padding both
    extremities with surrounding text.

    During stabilisation should support a ``_debug`` option to log which
    completion are return by the IPython completer and not found in Jedi in
    order to make upstream bug report.
    """
    warnings.warn(
        "`rectify_completions` is a provisional API (as of IPython 6.0). "
        "It may change without warnings. "
        "Use in corresponding context manager.",
        category=ProvisionalCompleterWarning,
        stacklevel=2,
    )

    completions = list(completions)
    if not completions:
        return
    starts = (c.start for c in completions)
    ends = (c.end for c in completions)

    new_start = min(starts)
    new_end = max(ends)

    seen_jedi = set()
    seen_python_matches = set()
    for c in completions:
        new_text = text[new_start : c.start] + c.text + text[c.end : new_end]
        if c._origin == "jedi":
            seen_jedi.add(new_text)
        elif c._origin == "IPCompleter.python_matches":
            seen_python_matches.add(new_text)
        yield Completion(
            new_start,
            new_end,
            new_text,
            type=c.type,
            _origin=c._origin,
            signature=c.signature,
        )
    diff = seen_python_matches.difference(seen_jedi)
    if diff and _debug:
        print("IPython.python matches have extras:", diff)


if sys.platform == "win32":
    DELIMS = " \t\n`!@#$^&*()=+[{]}|;'\",<>?"
else:
    DELIMS = " \t\n`!@#$^&*()=+[{]}\\|;:'\",<>?"

GREEDY_DELIMS = " =\r\n"


class CompletionSplitter:
    """An object to split an input line in a manner similar to readline.

    By having our own implementation, we can expose readline-like completion in
    a uniform manner to all frontends.  This object only needs to be given the
    line of text to be split and the cursor position on said line, and it
    returns the 'word' to be completed on at the cursor after splitting the
    entire line.

    What characters are used as splitting delimiters can be controlled by
    setting the ``delims`` attribute (this is a property that internally
    automatically builds the necessary regular expression).

    Attributes
    ----------
    _delims : str
        A string of delimiter characters.  The default value makes sense for
        IPython's most typical usage patterns.
    _delim_expr : str
        The expression (a normal string) to be compiled into a regular expression
        for actual splitting.  We store it as an attribute mostly for ease of
        debugging, since this type of code can be so tricky to debug.
    _delim_re : str
        The regular expression that does the actual splitting
    """

    _delims = DELIMS
    _delim_expr = None
    _delim_re = None

    def __init__(self, delims=None):
        """Wait we define self.delims here AND we have the property? How does that work?"""
        delims = CompletionSplitter._delims if delims is None else delims
        self.delims = delims

    @property
    def delims(self):
        """Return the string of delimiter characters."""
        return self._delims

    @delims.setter
    def delims(self, delims):
        """Set the delimiters for line splitting."""
        expr = "[" + "".join("\\" + c for c in delims) + "]"
        self._delim_re = re.compile(expr)
        self._delims = delims
        self._delim_expr = expr

    def split_line(self, line, cursor_pos=None):
        """Split a line of text with a cursor at the given position."""
        l = line if cursor_pos is None else line[:cursor_pos]
        return self._delim_re.split(l)[-1]


def get__all__entries(obj):
    """Returns the strings in the ``__all__`` attribute."""
    try:
        words = getattr(obj, "__all__")
    except BaseException:
        return []

    return [w for w in words if isinstance(w, str)]


def match_dict_keys(keys: List[str], prefix: str, delims: str):
    """Used by dict_key_matches, matching the prefix to a list of keys.

    Parameters
    ----------
    keys:
        list of keys in dictionary currently being completed.
    prefix:
        Part of the text already typed by the user. e.g. `mydict[b'fo`
    delims:
        String of delimiters to consider when finding the current key.

    Returns
    -------
    A tuple of three elements: ``quote``, ``token_start``, ``matched``, with
    ``quote`` being the quote that need to be used to close current string.
    ``token_start`` the position where the replacement should start occurring,
    ``matches`` a list of replacement/completion

    """
    if not prefix:
        return None, 0, [repr(k) for k in keys if isinstance(k, (str, bytes))]
    quote_match = re.search("[\"']", prefix)
    quote = quote_match.group()
    try:
        prefix_str = eval(prefix + quote, {})
    except Exception:
        return None, 0, []

    pattern = "[^" + "".join("\\" + c for c in delims) + "]*$"
    token_match = re.search(pattern, prefix, re.UNICODE)
    token_start = token_match.start()
    token_prefix = token_match.group()

    matched = []
    for key in keys:
        try:
            if not key.startswith(prefix_str):
                continue
        except (AttributeError, TypeError, UnicodeError):
            # Python 3+ TypeError on b'a'.startswith('a') or vice-versa
            continue

        # reformat remainder of key to begin with prefix
        rem = key[len(prefix_str) :]
        # force repr wrapped in '
        rem_repr = repr(rem + '"') if isinstance(rem, str) else repr(rem + b'"')
        if rem_repr.startswith("u") and prefix[0] not in "uU":
            # Found key is unicode, but prefix is Py2 string.
            # Therefore attempt to interpret key as string.
            try:
                rem_repr = repr(rem.encode("ascii") + '"')
            except UnicodeEncodeError:
                continue

        rem_repr = rem_repr[1 + rem_repr.index("'") : -2]
        if quote == '"':
            # The entered prefix is quoted with ",
            # but the match is quoted with '.
            # A contained " hence needs escaping for comparison:
            rem_repr = rem_repr.replace('"', '\\"')

        # then reinsert prefix from start of token
        matched.append("%s%s" % (token_prefix, rem_repr))
    return quote, token_start, matched


def cursor_to_position(text: str, line: int, column: int) -> int:
    """Convert the (line,column) position of the cursor in text.

    This is converted to an offset in a string.

    Parameters
    ----------
    text : str
        The text in which to calculate the cursor offset
    line : int
        Line of the cursor; 0-indexed
    column : int
        Column of the cursor 0-indexed

    Return
    ------
    Position of the cursor in ``text``, 0-indexed.

    See Also
    --------
    position_to_cursor: reciprocal of this function

    """
    lines = text.split("\n")
    assert line <= len(lines), "{} <= {}".format(str(line), str(len(lines)))

    return sum(len(l) + 1 for l in lines[:line]) + column


def position_to_cursor(text: str, offset: int) -> Tuple[int, int]:
    """
    Convert the position of the cursor in text (0 indexed) to a line
    number(0-indexed) and a column number (0-indexed) pair

    Position should be a valid position in 'text'.

    Parameters
    ----------
    text : str
        The text in which to calculate the cursor offset
    offset : int
        Position of the cursor in ``text``, 0-indexed.

    Returns
    -------
    (line, column) : (int, int)
        Line of the cursor; 0-indexed, column of the cursor 0-indexed

    See Also
    --------
    cursor_to_position : reciprocal of this function

    """
    assert 0 <= offset <= len(text), "0 <= %s <= %s" % (offset, len(text))

    before = text[:offset]
    blines = before.split("\n")  # ! splitnes trim trailing \n
    line = before.count("\n")
    col = len(blines[-1])
    return line, col


def _safe_isinstance(obj, module, class_name):
    """Checks if obj is an instance of module.class_name if loaded."""
    return module in sys.modules and isinstance(
        obj, getattr(import_module(module), class_name)
    )


def back_unicode_name_matches(text):
    """Match unicode characters back to unicode name

    This does  ``☃`` -> ``\\snowman``

    Note that snowman is not a valid python3 combining character but will be expanded.
    Though it will not recombine back to the snowman character by the completion machinery.

    This will not either back-complete standard sequences like \\n, \\b ...
    """
    if len(text) < 2:
        return "", ()
    maybe_slash = text[-2]
    if maybe_slash != "\\":
        return "", ()

    char = text[-1]
    # no expand on quote for completion in strings.
    # nor backcomplete standard ascii keys
    if char in string.ascii_letters or char in ['"', "'"]:
        return "", ()
    try:
        unic = unicodedata.name(char)
        return "\\" + char, ["\\" + unic]
    except KeyError:
        pass
    return "", ()


def back_latex_name_matches(text: str):
    """Match latex characters back to unicode name

    This does ``\\ℵ`` -> ``\\aleph``
    """
    if len(text) < 2:
        return "", ()
    maybe_slash = text[-2]
    if maybe_slash != "\\":
        return "", ()

    char = text[-1]
    # no expand on quote for completion in strings.
    # nor backcomplete standard ascii keys
    if char in string.ascii_letters or char in ['"', "'"]:
        return "", ()
    try:
        latex = reverse_latex_symbol[char]
        # '\\' replace the \ as well
        return "\\" + char, [latex]
    except KeyError:
        pass
    return "", ()


def _formatparamchildren(parameter) -> str:
    """Get parameter name and value from Jedi Private API.

    Jedi does not expose a simple way to get `param=value` from its API.

    Parameters
    ----------
    parameter : str
        Jedi's function `Param`

    Returns
    -------
    A string like 'a', 'b=1', ``*args``, ``**kwargs``.

    Raises
    ------
    :exc:`ValueError`.
    """
    description = parameter.description
    if not description.startswith("param "):
        raise ValueError(
            "Jedi function parameter description have change format."
            'Expected "param ...", found %r".' % description
        )
    return description[6:]


def _make_signature(completion) -> str:
    """Make the signature from a jedi completion.

    Parameter
    ---------
    completion: jedi.Completion
        object does not complete a function type

    Returns
    -------
    a string consisting of the function signature, with the parenthesis but
    without the function name.

    Example
    -------
    ``(a, *args, b=1, **kwargs)``

    """
    return "(%s)" % ", ".join(
        [f for f in (_formatparamchildren(p) for p in completion.params) if f]
    )
