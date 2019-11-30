# encoding: utf-8
"""System command aliases.

.. data:: shell_line_split

    This is used as the pattern for calls to split_user_input.

It's a compiled regular expression.:

``shell_line_split = re.compile(r'^(\s*)()(\S+)(.*$)')``

Authors:

* Fernando Perez
* Brian Granger

"""

# -----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
from logging import error
import os
import re
import sys

from traitlets.config.configurable import Configurable
from traitlets import List, Instance

from IPython.core.error import UsageError, AliasError, InvalidAliasError

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

# This is used as the pattern for calls to split_user_input.
shell_line_split = re.compile(r'^(\s*)()(\S+)(.*$)')


def default_aliases():
    """Return list of shell aliases to auto-define.

    Returns
    -------
    list
        Platform-specific list of aliases

    Notes
    -----
    The aliases defined here should be safe to use on a kernel
    regardless of what frontend it is attached to.  Frontends that use a
    kernel in-process can define additional aliases that will only work in
    their case.  For example, things like 'less' or 'clear' that manipulate
    the terminal should NOT be declared here, as they will only work if the
    kernel is running inside a true terminal, and not over the network.

    We define a useful set of ls aliases.  The GNU and BSD options are a little
    different, so we make aliases that provide as similar as possible
    behavior in ipython, by passing the right flags for each platform.

    .. versionchanged:: 7.10.0

        Added %l to all of the aliases because they shouldn't be missing that.

    """
    if os.name == 'posix':

        default_aliases = [
            ('mkdir', 'mkdir %l'),
            ('rmdir', 'rmdir %l'),
            ('mv', 'mv %l'),
            ('rm', 'rm %l'),
            ('cp', 'cp %l'),
            ('cat', 'cat %l'),
        ]
        if sys.platform.startswith('linux'):
            ls_aliases = [
                ('ls', 'ls -F --color %l'),
                # long ls
                ('ll', 'ls -F -o --color %l'),
                # ls normal files only
                ('lf', 'ls -F -o --color %l | grep ^-'),
                # ls symbolic links
                ('lk', 'ls -F -o --color %l | grep ^l'),
                # directories or links to directories,
                ('ldir', 'ls -F -o --color %l | grep /$'),
                # things which are executable
                ('lx', 'ls -F -o --color %l | grep ^-..x'),
            ]
        elif sys.platform.startswith('openbsd') or sys.platform.startswith(
                'netbsd'):
            # OpenBSD, NetBSD. The ls implementation on these platforms do not support
            # the -G switch and lack the ability to use colorized output.
            ls_aliases = [
                ('ls', 'ls -F'),
                # long ls
                ('ll', 'ls -F -l'),
                # ls normal files only
                ('lf', 'ls -F -l %l | grep ^-'),
                # ls symbolic links
                ('lk', 'ls -F -l %l | grep ^l'),
                # directories or links to directories,
                ('ldir', 'ls -F -l %l | grep /$'),
                # things which are executable
                ('lx', 'ls -F -l %l | grep ^-..x'),
            ]
        else:
            # BSD, OSX, etc.
            ls_aliases = [
                ('ls', 'ls -F -G'),
                # long ls
                ('ll', 'ls -F -l -G'),
                # ls normal files only
                ('lf', 'ls -F -l -G %l | grep ^-'),
                # ls symbolic links
                ('lk', 'ls -F -l -G %l | grep ^l'),
                # directories or links to directories,
                ('ldir', 'ls -F -G -l %l | grep /$'),
                # things which are executable
                ('lx', 'ls -F -l -G %l | grep ^-..x'),
            ]
        default_aliases = default_aliases + ls_aliases
    elif os.name in ['nt', 'dos']:
        default_aliases = [
            ('ls', 'dir /on %l'),
            ('ddir', 'dir /ad /on %l'),
            ('ldir', 'dir /ad /on %l'),
            ('mkdir', 'mkdir %l'),
            ('rmdir', 'rmdir %l'),
            ('echo', 'echo %l'),
            ('ren', 'ren %l'),
            ('copy', 'copy %l'),
        ]
    else:
        default_aliases = []

    return default_aliases


class Alias:
    """Callable object storing the details of one alias.

    Instances are registered as magic functions to allow use of aliases.

    .. todo:: More dunders. It would be sweet if we had a container we could ``+`` and ``-`` to.

    Attributes
    ----------
    blacklist : ...wait is that a dict?
        Seriously why is that a dict?
        Blacklisted keywords that can not be turned into aliases.

    """

    # Prepare blacklist
    blacklist = {'cd', 'popd', 'pushd', 'dhist', 'alias', 'unalias'}

    def __init__(self, shell, name, cmd):
        """Initialize an alias.

        Parameters
        ----------
        shell : TODO
            foo
        name
            bar
        cmd
            baz

        """
        self.shell = shell
        self.name = name
        self.cmd = cmd
        self.__doc__ = "Alias for `!{}`".format(cmd)
        self.nargs = self.validate()

    def validate(self):
        """Validate the alias, and return the number of arguments.

        Raises
        ------
        InvalidAliasError

        """
        if self.name in self.blacklist:
            raise InvalidAliasError("The name %s can't be aliased "
                                    "because it is a keyword or builtin." %
                                    self.name)
        try:
            caller = self.shell.magics_manager.magics['line'][self.name]
        except KeyError:
            pass
        else:
            if not isinstance(caller, Alias):
                raise InvalidAliasError(
                    "The name %s can't be aliased "
                    "because it is another magic command." % self.name)

        if not (isinstance(self.cmd, str)):
            raise InvalidAliasError("An alias command must be a string, "
                                    "got: %r" % self.cmd)

        nargs = self.cmd.count('%s') - self.cmd.count('%%s')

        if (nargs > 0) and (self.cmd.find('%l') >= 0):
            raise InvalidAliasError('The %s and %l specifiers are mutually '
                                    'exclusive in alias definitions.')

        return nargs

    def __repr__(self):
        return "<alias {} for {!r}>".format(self.name, self.cmd)

    def __call__(self, rest=''):
        cmd = self.cmd
        nargs = self.nargs
        # Expand the %l special to be the user's input line
        if cmd.find('%l') >= 0:
            cmd = cmd.replace('%l', rest)
            rest = ''

        if nargs == 0:
            if cmd.find('%%s') >= 1:
                cmd = cmd.replace('%%s', '%s')
            # Simple, argument-less aliases
            cmd = '%s %s' % (cmd, rest)
        else:
            # Handle aliases with positional arguments
            args = rest.split(None, nargs)
            if len(args) < nargs:
                raise UsageError(
                    'Alias <%s> requires %s arguments, %s given.' %
                    (self.name, nargs, len(args)))
            cmd = '%s %s' % (cmd % tuple(args[:nargs]), ' '.join(args[nargs:]))

        self.shell.system(cmd)


# -----------------------------------------------------------------------------
# Main AliasManager class
# -----------------------------------------------------------------------------


class AliasManager(Configurable):
    """Alias manager.

    Subclasses the :class:`traitlets.config.Configurable`.

    Attributes
    ----------
    default_aliases : list
        OS dependant aliases.
    user_aliases : list

    Properties
    ----------
    aliases

    """
    # is that supposed to say default_aliases or default_value?
    default_aliases = List(default_aliases()).tag(config=True)
    user_aliases = List(default_value=[],
                        help="User defined aliases").tag(config=True)

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC',
                     allow_none=True)

    def __init__(self, shell=None, **kwargs):
        """Initialize the class.

        Attributes
        ----------
        linemagics
            get_ipython().magics_manager.magics['line']

        """
        super().__init__(shell=shell, **kwargs)
        # For convenient access
        self.linemagics = self.shell.magics_manager.magics['line']
        self.init_aliases()

    def init_aliases(self):
        """Load default & user aliases."""
        for name, cmd in self.default_aliases + self.user_aliases:
            if cmd.startswith('ls ') and self.shell.colors == 'NoColor':
                cmd = cmd.replace(' --color', '')
            self.soft_define_alias(name, cmd)

    def __repr__(self):
        """ .. todo:: mixin reprlib.Repr and then use that for the representation."""
        return '{!r}\n'.format(self.__class__.__name__)

    @property
    def aliases(self):
        return [(n, func.cmd) for (n, func) in self.linemagics.items()
                if isinstance(func, Alias)]

    def soft_define_alias(self, name, cmd):
        """Define an alias, but don't raise on an AliasError."""
        try:
            self.define_alias(name, cmd)
        except AliasError as e:
            error("Invalid alias: %s" % e)

    def define_alias(self, name, cmd):
        """Define a new alias after validating it.

        Parameters
        ----------
        todo

        Raises
        ------
        This will raise an :exc:`AliasError` if there are validation
        problems.
        """
        caller = Alias(shell=self.shell, name=name, cmd=cmd)
        self.shell.magics_manager.register_function(caller,
                                                    magic_kind='line',
                                                    magic_name=name)

    def get_alias(self, name):
        """Return an alias, or None if no alias by that name exists."""
        aname = self.linemagics.get(name, None)
        return aname if isinstance(aname, Alias) else None

    def is_alias(self, name):
        """Return whether or not a given name has been defined as an alias."""
        return self.get_alias(name) is not None

    def undefine_alias(self, name):
        """Run :func:`del` on 'name'.

        Parameters
        ----------
        name : str
            Alias to delete

        Raises
        ------
        :exc:`ValueError`
            If 'name' isn't defined.

        """
        if self.is_alias(name):
            del self.linemagics[name]
        else:
            raise ValueError('%s is not an alias' % name)

    def clear_aliases(self):
        for name, cmd in self.aliases:
            self.undefine_alias(name)

    def retrieve_alias(self, name):
        """Retrieve the command to which an alias expands."""
        caller = self.get_alias(name)
        if caller:
            return caller.cmd
        else:
            raise ValueError('%s is not an alias' % name)
