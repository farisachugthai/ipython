"""Generate the key bindings for Sphinx documentation.

Good to knows:

dest is ipython/docs/source/config/shortcuts and it's where we store
csv files of shortcuts.

first defined var is single filter.


todo:: double check that passing an actual instance to
       create_ipython_shortcuts() wasn't the fix because then we won't need to rewrite this.


Changing this scripts output destination
========================================

Nov 01, 2019:
Remember that this script creates 2 csv files.

They're now going to be placed in source/api and I've already changed the location
that sphinx expects them to be at.

If you change the destination var in here, make sure it corresponds to the locations
sphinx is expecting in the doc :doc:`source/api/shortcuts`.

Frustratingly I think you also have to change it in the Makefile.
Check the files pointed to by the target for the autogen_shortcuts.

"""
from collections import Counter
import json
import logging
from os.path import abspath, dirname, join
from pathlib import Path
import sys

logging.basicConfig(level=logging.DEBUG)

from IPython.core.getipython import get_ipython
from IPython.terminal.shortcuts import create_ipython_shortcuts


def name(c):
    s = c.__class__.__name__
    if s == '_Invert':
        return '(Not: %s)' % name(c.filter)
    if s in log_filters.keys():
        return '(%s: %s)' % (log_filters[s], ', '.join(
            name(x) for x in c.filters))
    return log_filters[s] if s in log_filters.keys() else s


def most_common(lst, n=3):
    """Most common elements occurring more then `n` times."""
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


def common_docs(bindings=None):
    """Generate common docs for :class:`prompt_toolkit.key_binding.bindings`."""
    yield [kb.handler.__doc__ for kb in bindings]


def filter_shortcuts(ipy_bindings=None):
    """Yeah we shouldn't leave it like this."""
    for kb in common_docs(ipy_bindings):

        logging.debug('kb is: {}\ndir(kb) is: {}\n'.format(kb, dir(kb)))
        shortcut = ' '.join(
            [k if isinstance(k, str) else k.name for k in kb.keys])
        shortcut += shortcut.endswith('\\') and '\\' or ''
        if hasattr(kb.filter, 'filters'):
            flt = ' '.join(multi_filter_str(kb.filter))
        # else:
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
        # single_filter[(shortcut, name(kb.filter))] = sentencize(doc)
    yield shortcut


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


def dict_to_file(dictionary=None, filename=None, path_to_file=None):
    """Accepts Path objects for filename. Everythings optional."""
    if filename:
        if hasattr(filename, '__fspath__'):
            filename = filename.__fspath__
    else:
        return

    with open(filename, 'wt') as f:
        for k, v in dictionary.items():
            f.write(':kbd:`{}`\t\t{}\n'.format(k, v))


def running_in_ipython():
    ipython_keybindings = create_ipython_shortcuts(get_ipython())

    ipy_bindings = ipython_keybindings.bindings

    for i in ipy_bindings:
        shortcuts = filter_shortcuts(ipy_bindings)
    logging.debug(shortcuts)
    # honestly we won't need dict to file anymore. the generate output functions
    # pretty unnecessary too.


def main():
    here = Path(__file__)
    dest = Path('source', 'api', 'shortcuts')
    if not dest.is_dir():
        dest.mkdir()
        logging.debug('Creating dir: {}'.format(dest))

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

    # Uh yeah this fix only works if get_ipython() returns anything.

    if shell is not None:
        running_in_ipython()
        logging.debug('shell is : {}'.format(shell))
    else:
        sys.exit('you embedded a shell and it still came up none')

    # else:
    #     error_message = 'Are you running this in Jupyter? Please switch over to IPython to auto-generate the prompt_toolkit keybindings correctly.'
    #     sys.exit(error_message)


if __name__ == '__main__':
    main()
