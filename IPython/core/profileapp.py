"""An application for managing IPython profiles.

To be invoked as the ``ipython profile`` subcommand.

.. note:: For developers looking to extend the profile subcommand!

    The dict where your code can attach to the shell is in :class:`ProfileApp`.

Therefore it's noteworthy to see how we did this.

.. class:: ProfileApp

    IPython subcommand to work with profiles.

    .. attribute:: subcommands

        The `traitlets.traitlets.Dict` that maps the `profile` subcommands
        to their handlers.

Let's give an example.

On the command line, if I were to run ``ipython profile list``, ``list``
would be a subcommand of ``profile``.

If I wanted to extend the ``ipython profile`` functionality, I'd need to
register it in `ProfileApp.subcommands`.

Authors:

* Min RK

"""

# -----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------


import os

# -----------------------------------------------------------------------------
from importlib import import_module

# Imports
# -----------------------------------------------------------------------------
from textwrap import dedent

from traitlets import Bool, Dict, Unicode, observe
from traitlets.config.application import Application

from IPython.core.application import BaseIPythonApplication, base_flags
from IPython.core.profiledir import ProfileDir
from IPython.paths import get_ipython_dir, get_ipython_package_dir

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

create_help = """Create an IPython profile by name

Create an ipython profile directory by its name or
profile directory path. Profile directories contain
configuration, log and security related files and are named
using the convention 'profile_<name>'. By default they are
located in your ipython directory. Once created, you will
can edit the configuration files in the profile
directory to configure IPython. Most users will create a
profile directory by name,
`ipython profile create myprofile`, which will put the directory
in `<ipython_dir>/profile_myprofile`.
"""
list_help = """List available IPython profiles

List all available profiles, by profile location, that can
be found in the current working directly or in the ipython
directory. Profile directories are named using the convention
'profile_<profile>'.
"""
profile_help = """Manage IPython profiles

Profile directories contain
configuration, log and security related files and are named
using the convention 'profile_<name>'. By default they are
located in your ipython directory.  You can create profiles
with `ipython profile create <name>`, or see the profiles you
already have with `ipython profile list`

To get started configuring IPython, simply do:

$> ipython profile create

and IPython will create the default profile in <ipython_dir>/profile_default,
where you can edit ipython_config.py to start configuring IPython.

"""

_list_examples = "ipython profile list  # list all profiles"

_create_examples = """
ipython profile create foo         # create profile foo w/ default config files
ipython profile create foo --reset # restage default config files over current
ipython profile create foo --parallel # also stage parallel config files
"""

_main_examples = """
ipython profile create -h  # show the help string for the create subcommand
ipython profile list -h    # show the help string for the list subcommand

ipython locate profile foo # print the path to the directory for profile 'foo'
"""


# -----------------------------------------------------------------------------
# Profile Application Class (for `ipython profile` subcommand)
# -----------------------------------------------------------------------------


def list_profiles_in(path):
    """List profiles in a given root directory.

    .. caution:: Variable not in call signature that's initialized in the function.

        A list for 'profiles'.

    Parameters
    ----------
    path : str
        Directory to check.

    """
    profiles = []

    # for python 3.6+ rewrite to: with os.scandir(path) as dirlist:
    files = os.scandir(os.path.expanduser(path))
    for f in files:
        if f.is_dir() and f.name.startswith("profile_"):
            profiles.append(f.name.split("_", 1)[-1])

    # Keeps prepending an empty spot up front
    if len(profiles) > 0:
        if profiles[0] == "":
            profiles = profiles[1:]
    return profiles


def list_bundled_profiles():
    """List profiles that are bundled with IPython."""
    path = os.path.join(get_ipython_package_dir(), "core", "profile")
    profiles = []

    # for python 3.6+ rewrite to: with os.scandir(path) as dirlist:
    files = os.scandir(path)
    for profile in files:
        if profile.is_dir() and profile.name != "__pycache__":
            profiles.append(profile.name)
    return profiles


class ProfileLocate(BaseIPythonApplication):
    """A minimally useful class for printing the path to the profile dir."""

    description = "print the path to an IPython profile dir"

    def __init__(self, *args, **kwargs):
        super(ProfileLocate, self).__init__(*args, **kwargs)

    def parse_command_line(self, argv=None):
        """

        Parameters
        ----------
        argv :
        """
        super(ProfileLocate, self).parse_command_line(argv)
        if self.extra_args:
            self.profile = self.extra_args[0]

    def start(self):
        """How odd is it that this subapp's start method is printing?

        Maybe more importantly, do we ensure that this has a profile_dir
        attribute?
        """
        print(self.profile_dir.location)

    def __repr__(self):
        return self.start()


def _print_profiles(profiles):
    """print list of profiles, indented. todo: textwrap.indent"""
    for profile in profiles:
        print("    %s" % profile)


class ProfileList(Application):
    """Wrapped attributes with traitlets.Unicode and called textwrap.dedent.

    I'm really surprised that was never done before.

    .. warning:: Can't wrap with Unicode trait. We call splitlines on it later.

    """

    name = "ipython-profile"
    description = dedent(list_help)
    examples = dedent(_list_examples)

    aliases = Dict(
        {
            "ipython-dir": "ProfileList.ipython_dir",
            "log-level": "Application.log_level",
        }
    )

    flags = Dict(
        {
            "debug": (
                {"Application": {"log_level": 0}},
                "Set Application.log_level to 0, maximizing log output.",
            )
        }
    )

    ipython_dir = Unicode(
        get_ipython_dir(),
        help="""
        The name of the IPython directory. This directory is used for logging
        configuration (through profiles), history storage, etc. The default
        is usually $HOME/.ipython. This options can also be specified through
        the environment variable IPYTHONDIR.
        """,
    ).tag(config=True)

    def list_profile_dirs(self):
        """Lists profiles in the `IPYTHONDIR` and then the `os.path.curdir`.

        .. todo::
            We don't bundle profiles so i deleted that.
            Need to disambiguate between bundled and curdir profiles next.

        """
        profiles = list_profiles_in(self.ipython_dir)
        if profiles:
            print("Available profiles in %s:" % self.ipython_dir)
            _print_profiles(profiles)

        profiles = list_profiles_in(os.getcwd())
        if profiles:
            print("\nAvailable profiles in current directory (%s):" % os.getcwd())
            _print_profiles(profiles)

        print("\nTo use any of the above profiles, start IPython with:")
        print("    ipython --profile=<name>\n")

    def start(self):
        """Calls self.list_profile_dirs."""
        self.list_profile_dirs()


create_flags = {}
create_flags.update(base_flags)
# don't include '--init' flag, which implies running profile create in
# other apps
create_flags.pop("init")
create_flags["reset"] = (
    {"ProfileCreate": {"overwrite": True}},
    "reset config files in this profile to the defaults.",
)
create_flags["parallel"] = (
    {"ProfileCreate": {"parallel": True}},
    "Include the config files for parallel "
    "computing apps (ipengine, ipcontroller, etc.)",
)


class ProfileCreate(BaseIPythonApplication):
    """IPython Application with auto_create *config-files* set to the True.

    Attributes
    ----------
    parallel : :class:`~traitlets.Bool`
        Didn't realize you could implicitly create an ipyparallel from right
        here. Kinda hints that IPyParallel i a dependency thought right?

    A handful. Thankfully they're not grouped together at the top so I'll
    document it when I'm done fishing through this whole file to reorganize
    this classes attributes and put them together! :D

    """

    name = "ipython-profile"
    description = dedent(create_help)
    examples = dedent(_create_examples)
    auto_create = Bool(True, help="Why does this var exist if it isn't configurable?")
    flags = Dict(create_flags)

    parallel = Bool(
        False, help="whether to include parallel computing config files"
    ).tag(config=True)

    def _log_format_default(self):
        return "[ %(created)f : %(name)s : %(highlevel)s : %(message)s : ]"

    def _copy_config_files_default(self):
        """A method that returns True. I don't understand why it exists."""
        return True

    @observe("parallel")
    def _parallel_changed(self, change):
        """Handler for if the ipyparallel files change.

        ipyparallel is configured by the following files.:

        * ipcontroller_config.py
        * ipengine_config.py
        * ipcluster_config.py

        """
        parallel_files = [
            "ipcontroller_config.py",
            "ipengine_config.py",
            "ipcluster_config.py",
        ]
        if change["new"]:
            for cf in parallel_files:
                self.config_files.append(cf)
        else:
            for cf in parallel_files:
                if cf in self.config_files:
                    self.config_files.remove(cf)

    def parse_command_line(self, argv):
        """Parses the command line as passed by 'argv'.

        Differentiated from the superclasses method with.:

        >>> # accept positional arg as profile name
        >>> if self.extra_args:
            >>> self.profile = self.extra_args[0]

        What's the point of doing that if you can just
        unpack the args as a tuple? Kinda dumb you say? I'd agree.

        """
        super().parse_command_line(argv)
        # accept positional arg as profile name
        if self.extra_args:
            self.profile = self.extra_args[0]

    classes = [ProfileDir]

    def _import_app(self, app_path):
        """Import an app class."""
        name = app_path.rsplit(".", 1)[-1]
        try:
            app = import_module(app_path)
        except ImportError as e:
            self.log.warning(
                """Couldn't import {}, config file will be excluded
                          The cause of the ImportError was {}""".format(
                    e
                )
            )
            return
        except Exception:
            self.log.error("Unexpected error importing %s", name, exc_info=True)
            return
        else:
            return app

    def init_config_files(self):
        """Calls super().init_config_files so maybe a good candidate for a classmethod decorator?"""
        super().init_config_files()
        # use local imports, since these classes may import from here
        from IPython.terminal.ipapp import TerminalIPythonApp

        apps = [TerminalIPythonApp]
        for app_path in ("ipykernel.kernelapp.IPKernelApp",):
            app = self._import_app(app_path)
            if app is not None:
                apps.append(app)
        if self.parallel:
            from ipyparallel.apps.ipcontrollerapp import IPControllerApp
            from ipyparallel.apps.ipengineapp import IPEngineApp
            from ipyparallel.apps.ipclusterapp import IPClusterStart

            apps.extend(
                [IPControllerApp, IPEngineApp, IPClusterStart,]
            )
        for App in apps:
            app = App()
            app.config.update(self.config)
            app.log = self.log
            app.overwrite = self.overwrite
            app.copy_config_files = True
            app.ipython_dir = self.ipython_dir
            app.profile_dir = self.profile_dir
            app.init_config_files()

    def stage_default_config_file(self):
        """Does a subclass implement this? We only ``pass`` here."""
        pass


class ProfileApp(Application):
    """An example of an Application. Should probably refer to that.

    The object in this file doesn't define any attributes it uses in it's
    own methods.
    """

    name = "ipython profile"
    description = dedent(profile_help)
    examples = dedent(_main_examples)

    subcommands = Dict(
        {
            "create": (ProfileCreate, ProfileCreate.description.splitlines()[0]),
            "list": (ProfileList, ProfileList.description.splitlines()[0]),
            "locate": (ProfileLocate, ProfileLocate.description.splitlines()[0]),
        }
    )

    def start(self):
        """TODO: Is there a way to check if we're running with config['quiet'].

        Or can we build that because our help message is really long.
        """
        if self.subapp is None:
            self.log.warning(
                "No subcommand specified. Must specify one of: %s\n"
                % (self.subcommands.keys())
            )
            self.print_description()
            self.print_subcommands()
            self.exit(1)
        else:
            return self.subapp.start()
