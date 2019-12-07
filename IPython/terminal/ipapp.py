#!/usr/bin/env python
# encoding: utf-8
"""
The :class:`~IPython.core.application.Application` object for the command
line :command:`ipython` program.

.. tip:: I guess this is the main entry point.

    Yeah this file in particular is. Running the command IPython on the CLI
    imports this file and initializes the TerminalIPythonApp which kicks
    off everything else.

    I'm currently running into a problem where we keep sys.exiting with the 1
    exit status at the bottom so we have to figure out why that is.

"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import logging
import os
import sys
import warnings
from pathlib import Path

from IPython.core import release, usage
from IPython.core.crashhandler import CrashHandler
from IPython.core.formatters import PlainTextFormatter
from IPython.core.history import HistoryManager
from IPython.core.magics import LoggingMagics, ScriptMagics
from IPython.core.shellapp import (InteractiveShellApp, shell_aliases,
                                   shell_flags)

from IPython.paths import get_ipython_dir
from IPython.core.application import (BaseAliases, BaseIPythonApplication,
                                      base_aliases, base_flags)
from IPython.terminal.interactiveshell import TerminalInteractiveShell

from traitlets import Bool, List, Type, default, observe
from traitlets.config.application import boolean_flag, catch_config_error
from traitlets.config.loader import Config

# Ensure you comment this out later
logging.Filter()
logging.basicConfig(level=logging.WARNING,
                    format="%(created)f : %(module)s : %(levelname)s : %(message)s")

# This should probably be in ipapp.py.
# From IPython/__init__
dirname = Path().resolve()
root = dirname.parent
extension_dir = dirname.joinpath('extensions')
sys.path.append(extension_dir.__fspath__())

# -----------------------------------------------------------------------------
# Globals, utilities and helpers
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Crash handler for this application
# -----------------------------------------------------------------------------


class IPAppCrashHandler(CrashHandler):
    """sys.excepthook for IPython itself, leaves a detailed report on disk."""

    def __init__(self, app):
        contact_name = release.author
        contact_email = release.author_email
        bug_tracker = 'https://github.com/ipython/ipython/issues'
        super().__init__(app, contact_name, contact_email, bug_tracker)

    def make_report(self, traceback):
        """Return a string containing a crash report."""
        # Start with parent report
        report = [super().make_report(traceback)]

        # Add interactive-specific info we may have.WHAT IS WITH THE ABBREVIATIONS FFS
        report.append(self.section_sep + "History of session input:")
        for line in self.app.shell.user_ns['_ih']:
            report.append(line)
        report.append(
            '\n*** Last line of input (may not be in above history):\n')
        report.append(self.app.shell._last_input_line + '\n')

        return ''.join(report)


# -----------------------------------------------------------------------------
# Aliases and Flags
# -----------------------------------------------------------------------------

flags = dict(base_flags)
flags.update(shell_flags)
frontend_flags = {}
addflag = lambda *args: frontend_flags.update(boolean_flag(*args))
addflag('simple-prompt', 'TerminalInteractiveShell.simple_prompt',
        "Force simple minimal prompt using `raw_input`",
        "Use a rich interactive prompt with prompt_toolkit",
        )

addflag('banner', 'TerminalIPythonApp.display_banner',
        "Display a banner upon starting IPython.",
        "Don't display a banner upon starting IPython.")
addflag(
    'confirm-exit', 'TerminalInteractiveShell.confirm_exit',
    """Set to confirm when you try to exit IPython with an EOF (Control-D
in Unix, Control-Z/Enter in Windows). By typing 'exit' or 'quit',
you can force a direct exit without any confirmation.""",
    "Don't prompt the user when exiting.")
addflag('term-title', 'TerminalInteractiveShell.term_title',
        "Enable auto setting the terminal title.",
        "Disable auto setting the terminal title.")


def setup_classic_config():
    """No point in these being globals if you don't use the classic prompt."""
    classic_config = Config()
    classic_config.InteractiveShell.cache_size = 0
    classic_config.PlainTextFormatter.pprint = False
    classic_config.TerminalInteractiveShell.prompts_class = 'IPython.terminal.prompts.ClassicPrompts'
    classic_config.InteractiveShell.separate_in = ''
    classic_config.InteractiveShell.separate_out = ''
    classic_config.InteractiveShell.separate_out2 = ''
    classic_config.InteractiveShell.colors = 'NoColor'
    classic_config.InteractiveShell.xmode = 'Plain'
    return classic_config


# JFC it was hard getting this to be a recognizable data structure and format it well
frontend_flags = {
    'classic': (setup_classic_config(), "Gives IPython a similar feel to the classic Python prompt."),
    'quick': ({'TerminalIPythonApp': {'quick': True}}, "Enable quick startup with no config files."),
    'i': ({'TerminalIPythonApp': {'force_interact': True}}, """
If running code from the command line, become interactive afterwards.
It is often useful to follow this with `--` to treat remaining flags as
script arguments.
""")
}
# log doesn't make so much sense this way anymore
# ...does that say paa?
# paa('--log','-l',
#     action='store_true', dest='InteractiveShell.logstart',
#     help="Start logging to the default log file (./ipython_log.py).")
#
# # quick is harder to implement

flags.update(frontend_flags)

aliases = base_aliases
aliases.update(shell_aliases)

# -----------------------------------------------------------------------------
# Main classes and functions
# -----------------------------------------------------------------------------


class LocateIPythonApp(BaseIPythonApplication):
    """A class that literally only has 1 subcommand. Why?"""
    description = """Print the path to the IPython dir."""
    subcommands = dict(profile=(
        'IPython.core.profileapp.ProfileLocate',
        "Print the path to an IPython profile directory.",
    ), )

    def start(self):
        """Why not print AND return the value?"""
        if self.subapp is not None:
            return self.subapp.start()
        else:
            print(self.ipython_dir)
            # return self.ipython_dir


class TerminalIPythonApp(BaseIPythonApplication, InteractiveShellApp):
    """A mixin class similar to the one defined in IPython.core.application.

    Difference being that this allows more terminal specific configurations.
    However I still really don't get the difference between apps and shells.

    As far as I can tell so far, apps are a more general concept as they
    inherit from traitlets.config.Configurable and are the actual entry
    point of this program.

    .. bug:: Running ``ipython --profile=None`` crashes the application.

    Attributes
    ----------
    force_interact : Bool
        If there is code of files to run from the cmd line, don't interact
        unless the --i flag (App.force_interact) is true.

    """
    name = u'ipython'
    # description = usage.cl_usage
    # crash_handler_class = IPAppCrashHandler
    examples = """
ipython --matplotlib       # enable matplotlib integration
ipython --matplotlib=qt    # enable matplotlib integration with qt4 backend

ipython --log-level=DEBUG  # set logging to DEBUG
ipython --profile=foo      # start with profile foo

ipython profile create foo # create profile foo w/ default config files
ipython help profile       # show the help for the profile subcmd

ipython locate             # print the path to the IPython directory
ipython locate profile foo # print the path to the directory for profile `foo`
"""

    flags = flags
    aliases = aliases
    classes = List()
    # apparently self hasn't been defined yet
    # classes = List(self._classes_default(),
    # help='Available classes').tag(config=False)

    interactive_shell_class = Type(
        klass=object,
        # use default_value otherwise which only allow subclasses.
        default_value=TerminalInteractiveShell,
        help="Class to use to instantiate the TerminalInteractiveShell object. Useful for custom Frontends"
    ).tag(config=True)

    @default('classes')
    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available.

        But ffs can't we generate that dynamically? We have to modify that
        `StoreMagics` was deprecated in like 4 spots and it's not gonna be
        clean or easy.

        Also I wanna point out that the IPCompleter is only used in one spot
        in this module. It's right here, and this doesn't feel like the most
        important use in the world.
        """
        from IPython.core.completer import IPCompleter
        from IPython.core.profiledir import ProfileDir
        return [
            InteractiveShellApp,  # ShellApp comes before TerminalApp, because
            self.__class__,  # it will also affect subclasses (e.g. QtConsole)
            TerminalInteractiveShell,
            HistoryManager,
            ProfileDir,
            PlainTextFormatter,
            IPCompleter,
            ScriptMagics,
            LoggingMagics,
        ]

    subcommands = dict(
        profile=("IPython.core.profileapp.ProfileApp",
                 "Create and manage IPython profiles."),
        kernel=("ipykernel.kernelapp.IPKernelApp",
                "Start a kernel without an attached frontend."),
        locate=("IPython.terminal.ipapp.LocateIPythonApp",
                "LocateIPythonApp.description"),
        history=("IPython.core.historyapp.HistoryApp",
                 "Manage the IPython history database."),
    )

    # *do* autocreate requested profile, but don't create the config file.
    auto_create = Bool(True)
    # configurables
    quick = Bool(
        False,
        help="Skipping the loading of config files.").tag(config=True)

    @observe('quick')
    def _quick_changed(self, change):
        if change['new']:
            self.load_config_file = lambda *a, **kw: None

    display_banner = Bool(
        True, help="Whether to display a banner upon starting IPython.").tag(
            config=True)

    force_interact = Bool(
        False,
        help="""If a command or file is given via the command-line,
        e.g. 'ipython foo.py', start an interactive shell after executing the
        file or command.
        Otherwise the shell will not run in interactive mode
        unless the flag, representing 'App.force_interact', is given on the command line.
        Defaults to False.""").tag(config=True)

    @observe('force_interact')
    def _force_interact_changed(self, change):
        if change['new']:
            self.interact = True

    @observe('file_to_run', 'code_to_run', 'module_to_run')
    def _file_to_run_changed(self, change):
        """It's possible that this block of code literally never executes.

        Look at upstream/master and notice that their version of this
        function is indented correctly.
        Why doesn't that raise a SyntaxError?
        """
        new = change['new']
        if new:
            self.something_to_run = True
        if new and not self.force_interact:
            self.interact = False

    # internal, not-configurable
    something_to_run = Bool(False)

    def parse_command_line(self, argv=None):
        """Override to allow old '-pylab' flag with deprecation warning"""
        argv = sys.argv[1:] if argv is None else argv

        if '-pylab' in argv:
            # deprecated `-pylab` given,
            # warn and transform into current syntax
            argv = argv[:]  # copy, don't clobber
            idx = argv.index('-pylab')
            warnings.warn(
                "`-pylab` flag has been deprecated.\n"
                "    Use `--matplotlib <backend>` and import pylab manually.")
            argv[idx] = '--pylab'

        return super().parse_command_line(argv)

    def _trycatch(self, line, else_to_run=None):
        """This is done so many times in this repo why not make it official?"""
        try:
            line
        except ImportError as e:
            self.log.warning('ImportError: {}'.format(e.tb_frame))
        except KeyboardInterrupt:
            self.log.warning('Interrupted!')
        except EOFError:
            self.log.warning('EOFError!')
        except BaseException as e:
            self.log.error('Error: {}'.format(e.tb_frame))
            return
        else:
            if else_to_run is not None:
                else_to_run

    @catch_config_error
    def initialize(self, argv=None):
        """Do actions after construct, but before starting the app.

        Returns
        -------
        None
            If subapp is not None. Simply start the subapp as there's no need
            to continue initializing.

        """
        super().initialize(argv)

        if self.subapp is not None:
            # don't bother initializing further, starting subapp
            return

        # only gets called like 1 or 2 times in startup but that gets old fast
        logging.info('{}: Extra args was:: {}'.format(
            __file__, self.extra_args))

        if self.extra_args and not self.something_to_run:
            self.file_to_run = self.extra_args[0]
        self._trycatch(self.init_path())
        # create the shell
        self._trycatch(self.init_shell())
        # and draw the banner
        self._trycatch(self.init_banner())
        # Now a variety of things that happen after the banner is printed.
        self.init_gui_pylab()
        self.init_extensions()
        # Gets called from shellapp
        self.init_code()

    def init_shell(self):
        """Initialize the InteractiveShell instance.

        Create an InteractiveShell instance.

        shell.display_banner should always be False for the terminal
        based app, because we call shell.show_banner() by hand below
        so the banner shows *before* all extension loading stuff.

        Wait why doesn't master have the config listed as getting passed to the shell??
        """
        self.shell = self.interactive_shell_class.instance(
            parent=self,
            config=self.config,
            profile_dir=self.profile_dir,
            ipython_dir=self.ipython_dir,
            user_ns=self.user_ns)
        self.shell.configurables.append(self)

    def init_banner(self):
        """Optionally display the banner."""
        if self.display_banner and self.interact:
            self.shell.show_banner()
        # Make sure there is a space below the banner.
        if self.log_level <= logging.INFO:
            print()

    def _pylab_changed(self, name, old, new):
        """Replace --pylab='inline' with --pylab='auto'"""
        if new == 'inline':
            warnings.warn("'inline' not available as pylab backend, "
                          "using 'auto' instead.")
            self.pylab = 'auto'

    def start(self):
        """Begins the mainloop.

        Relies on self.interact which is defined in the
        :mod:`IPython.core.shellapp` file and that class.
        """
        if hasattr(self, 'subapp'):
            if self.subapp is not None:
                return self.subapp.start()
        else:
            logging.error('terminal/ipapp: InteractiveApp does not have subapp attribute')

        # perform any prexec steps:
        if self.interact:
            self.log.info("Starting IPython's mainloop...")
            self.shell.mainloop()
        else:
            # self.log.debug("IPython not interactive...")
            # we're about to sys.exit don't just mark that as debug
            self.log.warning(
                'IPython not interactive. Here is the last execution; result.\n{}'
                .format(self.shell.last_execution_result))
            if not self.shell.last_execution_succeeded:
                self.log.error(
                    'terminal/ipapp: The sys.exit came from InteractiveShellApp.start. Your welcome.')
                sys.exit(1)


def load_default_config(ipython_dir=None):
    """Load the default config file from the default ipython_dir.

    This is useful for embedded shells.

    Parameters
    ----------
    ipython_dir : str (path-like), optional
        The directory where IPython config files live. If `None`, then
        `IPython.paths.get_ipython_dir` is queried.

    Returns
    -------
    TerminalIPythonApp.config : traitlets.config.config
        I guess that'd be the type but idk.

    """
    ipython_dir = ipython_dir or get_ipython_dir()

    profile_dir = os.path.join(ipython_dir, 'profile_default')
    app = TerminalIPythonApp()
    app.config_file_paths.append(profile_dir)
    app.load_config_file()
    return app.config


launch_new_instance = TerminalIPythonApp.launch_instance


if __name__ == '__main__':
    launch_new_instance()
