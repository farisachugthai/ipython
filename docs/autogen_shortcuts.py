"""Generate the key bindings for Sphinx documentation.

So this code is outrageously difficult to understand for no reason at all.

I'm running it through the debugger and piece by piece gonna document what you need to know.

Start with the ifmain.

here is the current directory. ipython/docs

dest is ipython/docs/source/config/shortcuts and it's where we store
csv files of shortcuts.

first defined var is single filter.

it's a dict. that's odd.

it's a dict but its always gonna be a single item dict. nah i guess it makes sense that it's a mapping.

reasonably it makes more sense than all those fucking list of tuples we have all over here.

NICE! I recovered a handful of the keybindings without trying
because **THIS MODULE IS SO FUCKED UP IT ACCIDENTALLY SHAVES A BUNCH OFF**.

todo:: double check that passing an actual instance to create_ipython_shortcuts() wasn't the fix because then we won't need to rewrite this.

I kinda want to just to get rid of this debaucle anyway though....

"""
import json
from os.path import abspath, dirname, join
import sys

from IPython.core.get_ipython import get_ipython
from IPython.terminal.shortcuts import create_ipython_shortcuts


def name(c):
    s = c.__class__.__name__
    if s == '_Invert':
        return '(Not: %s)' % name(c.filter)
    if s in log_filters.keys():
        return '(%s: %s)' % (log_filters[s], ', '.join(
            name(x) for x in c.filters))
    return log_filters[s] if s in log_filters.keys() else s


def sentencize(s):
    """Extract first sentence."""
    s = s.replace('\n', ' ').strip().split('.')
    s = s[0] if len(s) else s
    try:
        return " ".join(s.split())
    except AttributeError:
        return s


def most_common(lst, n=3):
    """Most common elements occurring more then `n` times."""
    from collections import Counter

    c = Counter(lst)
    return [k for (k, v) in c.items() if k and v > n]


def multi_filter_str(flt):
    """Yield readable conditional filter."""
    assert hasattr(flt, 'filters'), 'Conditional filter required'
    yield name(flt)


log_filters = {'_AndList': 'And', '_OrList': 'Or'}
log_invert = {'_Invert'}


class _DummyTerminal:
    """Used as a buffer to get prompt_toolkit bindings."""
    handle_return = None
    input_transformer_manager = None
    display_completions = None


# Wait i confued myself and i know this is dumb but how od you make a generator?
def common_docs(bindings=None):
    """Generate common docs for :class:`prompt_toolkit.key_binding.bindings`."""
    return [kb.handler.__doc__ for kb in bindings]


def needs_refactoring(ipy_bindings=None):
    """Yeah we shouldn't leave it like this."""
    single_filter = {}
    multi_filter = {}
    for kb in ipy_bindings:
        doc = kb.handler.__doc__
        if not doc or doc in dummy_docs:
            continue

        shortcut = ' '.join(
            [k if isinstance(k, str) else k.name for k in kb.keys])
        shortcut += shortcut.endswith('\\') and '\\' or ''
        if hasattr(kb.filter, 'filters'):
            flt = ' '.join(multi_filter_str(kb.filter))
            multi_filter[(shortcut, flt)] = sentencize(doc)
        else:
            # This one line of code.
            # 1) Run doc through the sentencize function
            # 2) Unpack the output into the LHS
            # 3) The output gets unpacked into a dict named single_filter
            # 4) The keys of single filter? A list. As usual.
            # 5) Lol no. The list is a tuple of a str and the output of
            # 6) kb.filter as input to the name() function.
            # 7) kb is the element in the iterable of ipy_bindings and filter is a prompt_toolkit non-data descriptor.
            # Point being? WHY THE FUCK IS THIS ONLY ONE LINE OF CODE I HAVE NO IDEA WHAT'S GOING ON???
            # HOW DO YOU DEBUG THIS????
            single_filter[(shortcut, name(kb.filter))] = sentencize(doc)


def sort_key(dictionary):
    """I'm gonna actually document what the fuck is going on.

    Like why did the original feel the need to cast everything to
    `str` btw? Goddamn this mod is making me so unreasonably angry.

    Oh shit. I just realized how difficult this is gonna be.
    We shouldn't assume a dictionary maintains order.
    we have to instantiate a collections.OrderedDict()

    Nah fuck that we could port it over to json.

    Wait why does this save as a csv in the first place?

    Oh right CSV table.

    Can we import csv and then utilize a class from there like this is
    dumb.

    Parameters
    ----------
    dictionary : dict
        `dict` to sort

    Returns
    -------
    json

    """
    return json.dumps(dictionary, sort_keys=True)


def generate_output():
    """Create the final output.

    .. todo:: Should refactor so that it takes a parameter.

        Could make this function ``dict_to_file`` and then ask for
        a dict as a parameter and write it to a file with an optional arg
        for a path to prepend. path=None and we call it with path=dest?

        I like it.

    """
    with open(join(dest, 'single_filtered.csv'), 'w') as csv:
        for k, v in single_filter.items():
            csv.write(':kbd:`{}`\t{}\t{}\n'.format(k[0], k[1], v))

    with open(join(dest, 'multi_filtered.csv'), 'w') as csv:
        for k, v in multi_filter.items():
            csv.write(':kbd:`{}`\t{}\t{}\n'.format(k[0], k[1], v))


def main():
    """Like why did so much of this HAVE to be executed in the global namespace?"""
    # I think vscode just changed the lambda to a def.
    # def sort_key(k): return (str(k[0][1]), str(k[0][0]))
    # I got something better

    here = abspath(dirname(__file__))
    dest = join(here, 'source', 'config', 'shortcuts')
    shell = get_ipython()

    if shell is None:
        # we need to start a dummy shell
        from IPython.terminal.embed import InteractiveShellEmbed
        shell = InteractiveShellEmbed()
        if hasattr(shell, 'dummy_mode'):
            shell.dummy_mode = True
        else:
            print(shell)
            print(type(shell))
    # If you run create_ipython_shortcuts(ZMQInteractiveShell()) from the Jupyter console, the first error is for this specifically.
    # if hasattr(shell, 'display_completions'):
        # ALRIGHT. So at least all that random global code is guarded a little.

        # how does this line of code work???? we didn't give it an ipython instance???
        # ipy_bindings = create_ipython_shortcuts(_DummyTerminal()).bindings

        # Let's break up the steps as much as possible I'm gonna need a while to debug this bs
    ipython_keybindings = create_ipython_shortcuts(get_ipython())

    ipy_bindings = ipython_keybindings.bindings

    needs_refactoring(ipy_bindings)

    # else:
    #     error_message = 'Are you running this in Jupyter? Please switch over to IPython to auto-generate the prompt_toolkit keybindings correctly.'
    #     sys.exit(error_message)


if __name__ == '__main__':
    main()
