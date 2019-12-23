# -*- coding: utf-8 -*-
"""IPython Test Process Controller

This module runs one or more subprocesses which will actually run the IPython
test suite.

Also it's really quietly dependant on coverage. Let's add that to the requirements.

"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import argparse
from codecs import decode
import logging
import multiprocessing.pool
import os
import platform
import shutil
import signal
import stat
import subprocess
import sys
import time

iplogger = logging.getLogger(name=__name__)

from IPython.utils.path import compress_user
from IPython.utils.sysinfo import get_sys_info
from IPython.utils.tempdir import TemporaryDirectory

from IPython.testing.iptest import StreamCapturer, have
from IPython.testing.iptest import test_group_names as py_test_group_names
from IPython.testing.iptest import test_sections


class TestController:
    """Run tests in a subprocess.

    I don't know why the following were comments.

    Attributes
    ----------
    section : str, optional
        IPython test suite to be executed.
    cmd : list
        command line arguments to be executed
    env : dict
        extra environment variables to set for the subprocess
    dirs : list
        `tempfile.TemporaryDirectory` instances to clear up when the
        process finishes
    process : :class:`subprocess.Popen` instance
        The instance of the tests running.
    stdout : str
        process stdout+stderr

    """

    section = None
    process = None

    def __init__(self, cmd=None, env=None, dirs=None, buffer_output=False):
        """Bind self.cmd to an empty list, env to a dict, and dirs to list.

        Adding in the stdout capturer because we can define all the needed
        attributes right in init.
        """
        self.cmd = cmd or []
        self.env = self.init_env(additional_vars=env)
        self.dirs = dirs or []
        self.buffer_output = buffer_output
        self.stdout_capturer = StreamCapturer(echo=(not self.buffer_output))

    def setUp(self):
        """Create temporary directories etc.

        This is only called when we know the test group will be run. Things
        created here may be cleaned up by self.cleanup().
        """
        pass

    def init_env(self, additional_vars=None) -> dict:
        user_env = os.environ.copy()
        if additional_vars is None:
            additional_vars = {}
        user_env.update(additional_vars)
        return user_env

    def launch(self, buffer_output=False, capture_output=False):
        """Checks if we're capturing output

        Parameters
        ----------
        buffer_output : bool
        capture_output : bool
            No idea why these are 2 separate parameters.
        """
        logging.debug("*** ENV:", self.env)
        logging.debug("*** CMD:", self.cmd)
        if buffer_output:
            capture_output = True
        self.stdout_capturer.start()
        stdout = c.writefd if capture_output else None
        stderr = subprocess.STDOUT if capture_output else None
        self.process = subprocess.Popen(
            self.cmd, stdout=stdout, stderr=stderr, env=self.env
        )

    def wait(self):
        """

        Returns
        -------

        """
        self.process.wait()
        self.stdout_capturer.halt()
        self.stdout = self.stdout_capturer.get_buffer()
        return self.process.returncode

    def cleanup_process(self):
        """Cleanup on exit by killing any leftover processes."""
        subp = self.process
        if subp is None or (subp.poll() is not None):
            return  # Process doesn't exist, or is already dead.

        try:
            print("Cleaning up stale PID: %d" % subp.pid)
            subp.kill()
        except subprocess.CalledProcessError:
            # This module only exports 1 error so catch that and not everything else
            # This is just a best effort, if we fail or the process was
            # really gone, ignore it.
            pass
        else:
            for i in range(10):
                if subp.poll() is None:
                    time.sleep(0.1)
                else:
                    break

        if subp.poll() is None:
            # The process did not die...
            print("... failed. Manual cleanup may be required.")

    def cleanup(self):
        """Kill process if it's still alive, and clean up temporary directories"""
        self.cleanup_process()
        for td in self.dirs:
            if getattr(td, "cleanup", None):
                td.cleanup()
            else:
                try:
                    shutil.rmtree(td)
                except PermissionError:
                    iplogger.warning("PermissionError in cleanup")
                except OSError:
                    iplogger.warning("OSError in cleanup")

    def __del__(self):
        return self.cleanup()


class PyTestController(TestController):
    """Run Python tests using IPython.testing.iptest.

    Attributes
    ----------
    pycmd : str
        Python command to execute in subprocess

    """

    def __init__(self, section, options, *args, **kwargs):
        """Create new test runner."""
        super().__init__(*args, **kwargs)
        self.section = section
        # pycmd is put into cmd[2] in PyTestController.launch()
        self.cmd = [sys.executable, "-c", None, section]
        self.pycmd = "from IPython.testing.iptest import run_iptest; run_iptest()"
        self.options = options

        ipydir = TemporaryDirectory()
        self.dirs.append(ipydir)
        self.env["IPYTHONDIR"] = ipydir.name

        self.workingdir = TemporaryDirectory()
        self.dirs.append(self.workingdir)

        self.env["IPTEST_WORKING_DIR"] = self.workingdir.name
        # This means we won't get odd effects from our own matplotlib config
        self.env["MPLCONFIGDIR"] = self.workingdir.name
        # For security reasons (http://bugs.python.org/issue16202), use
        # a temporary directory to which other users have no access.
        self.env["TMPDIR"] = self.workingdir.name

        # Uh this probably needed to be here and not in setup.
        # Add a non-accessible directory to PATH (see gh-7053)
        self.noaccess = os.path.join(self.workingdir.name, "_no_access_")
        os.mkdir(self.noaccess, 0)
        PATH = os.environ.get("PATH", "")
        if PATH:
            PATH = self.noaccess + os.pathsep + PATH
        else:
            PATH = self.noaccess
        self.env["PATH"] = PATH

    def setup(self):
        """Create a TemporaryDirectory, set the workingdir to a different one."""

        # From options:
        if self.options.xunit:
            self.add_xunit()
        if self.options.coverage:
            self.add_coverage()
        self.env["IPTEST_SUBPROC_STREAMS"] = self.options.subproc_streams
        self.cmd.extend(self.options.extra_args)

    def cleanup(self):
        """
        Make the non-accessible directory created in setup() accessible
        again, otherwise deleting the workingdir will fail.
        """
        # os.chmod(self.noaccess, stat.S_IRWXU)
        super().cleanup()

    @property
    def will_run(self):
        """

        Returns
        -------

        """
        try:
            return test_sections[self.section].will_run
        except KeyError:
            return True

    def add_xunit(self):
        """

        """
        xunit_file = os.path.abspath(self.section + ".xunit.xml")
        self.cmd.extend(["--with-xunit", "--xunit-file", xunit_file])

    def add_coverage(self):
        """

        """
        try:
            sources = test_sections[self.section].includes
        except KeyError:
            sources = ["IPython"]

        coverage_rc = (
            "[run]\n" "data_file = {data_file}\n" "source =\n" "  {source}\n"
        ).format(
            data_file=os.path.abspath(".coverage." + self.section),
            source="\n  ".join(sources),
        )
        config_file = os.path.join(self.workingdir.name, ".coveragerc")
        with open(config_file, "w") as f:
            f.write(coverage_rc)

        self.env["COVERAGE_PROCESS_START"] = config_file
        self.pycmd = "import coverage; coverage.process_startup(); " + self.pycmd

    def launch(self, buffer_output=False):
        """

        Parameters
        ----------
        buffer_output :
        """
        self.cmd[2] = self.pycmd
        if buffer_output:
            super().launch(buffer_output=buffer_output)
        else:
            super().launch()


def prepare_controllers(options):
    """
    Returns two lists of TestController instances, those to run, and those
    not to run.
    """
    testgroups = options.testgroups
    if not testgroups:
        testgroups = py_test_group_names

    controllers = [PyTestController(name, options) for name in testgroups]

    to_run = [c for c in controllers if c.will_run]
    not_run = [c for c in controllers if not c.will_run]
    return to_run, not_run


def do_run(controller, buffer_output=True):
    """Setup and run a test controller.

    If buffer_output is True, no output is displayed, to avoid it appearing
    interleaved. In this case, the caller is responsible for displaying test
    output on failure.

    Returns
    -------
    controller : TestController
        The same controller as passed in, as a convenience for using map() type
        APIs.
    exitcode : int
        The exit code of the test subprocess. Non-zero indicates failure.
    """
    try:
        try:
            controller.setup()
            controller.launch(buffer_output=buffer_output)
        except Exception:
            import traceback

            traceback.print_exc()
            return controller, 1  # signal failure

        exitcode = controller.wait()
        return controller, exitcode

    except KeyboardInterrupt:
        return controller, -signal.SIGINT
    finally:
        controller.cleanup()


def report():
    """Return a string with a summary report of test-related variables."""
    inf = get_sys_info()
    out = []

    def _add(name, value):
        out.append((name, value))

    _add("IPython version", inf["ipython_version"])
    _add("IPython commit", "{} ({})".format(inf["commit_hash"], inf["commit_source"]))
    _add("IPython package", inf["ipython_path"])
    _add("Python version", sys.version)
    _add("sys.executable", sys.executable)
    _add("Platform", inf["platform"])

    width = max(len(n) for (n, v) in out)
    out = ["{:<{width}}: {}\n".format(n, v, width=width) for (n, v) in out]

    avail = []
    not_avail = []

    for k, is_avail in have.items():
        if is_avail:
            avail.append(k)
        else:
            not_avail.append(k)

    if avail:
        out.append("\nTools and libraries available at test time:\n")
        avail.sort()
        out.append("   " + " ".join(avail) + "\n")

    if not_avail:
        out.append("\nTools and libraries NOT available at test time:\n")
        not_avail.sort()
        out.append("   " + " ".join(not_avail) + "\n")

    return "".join(out)


def run_iptestall(options):
    """Run the entire IPython test suite by calling nose and trial.

    This function constructs :class:`IPTester` instances for all IPython
    modules and package and then runs each of them.  This causes the modules
    and packages of IPython to be tested each in their own subprocess using
    nose.

    Parameters
    ----------
    options : dict
        Apparently fast means run sequentially with 1 thread.

    """
    to_run, not_run = prepare_controllers(options)

    def justify(ltext, rtext, width=70, fill="-"):
        """

        Parameters
        ----------
        ltext :
        rtext :
        width :
        fill :

        Returns
        -------

        """
        ltext += " "
        rtext = (" " + rtext).rjust(width - len(ltext), fill)
        return ltext + rtext

    # Run all test runners, tracking execution time
    failed = []
    t_start = time.time()

    if platform.platform().startswith("Win"):
        if not hasattr(options, "fast"):
            options.__setattr__("fast", 1)

    if options.fast == 1:
        # This actually means sequential, i.e. with 1 job
        for controller in to_run:
            print("Test group:", controller.section + "\n")
            sys.stdout.flush()  # Show in correct order when output is piped
            controller, res = do_run(controller, buffer_output=False)
            if res:
                failed.append(controller)
                if res == -signal.SIGINT:
                    print("Interrupted")
                    break

    else:
        # Run tests concurrently
        try:
            pool = multiprocessing.pool.ThreadPool(options.fast)
            for (controller, res) in pool.imap_unordered(do_run, to_run):
                res_string = "OK" if res == 0 else "FAILED"
                print(justify("Test group: " + controller.section, res_string))
                if res:
                    print(decode(controller.stdout))
                    failed.append(controller)
                    if res == -signal.SIGINT:
                        print("Interrupted")
                        break
        except KeyboardInterrupt:
            return

    for controller in not_run:
        print(justify("Test group: " + controller.section, "NOT RUN"))

    t_end = time.time()
    t_tests = t_end - t_start
    nrunners = len(to_run)
    nfail = len(failed)
    # summarize results
    print("_" * 70)
    print("Test suite completed for system with the following information:")
    print(report())
    took = "Took %.3fs." % t_tests
    print("Status: ", end="")
    if not failed:
        print("OK (%d test groups)." % nrunners, took)
    else:
        # If anything went wrong, point out what command to rerun manually to
        # see the actual errors and individual summary
        failed_sections = [c.section for c in failed]
        print(
            "ERROR - {} out of {} test groups failed ({}).".format(
                nfail, nrunners, ", ".join(failed_sections)
            ),
            took,
        )
        print()
        print("You may wish to rerun these, with:")
        print("  iptest", *failed_sections)
        print()

    if options.coverage:
        from coverage import coverage, CoverageException

        cov = coverage(data_file=".coverage")
        cov.combine()
        cov.save()

        # Coverage HTML report
        if options.coverage == "html":
            html_dir = "ipy_htmlcov"
            shutil.rmtree(html_dir, ignore_errors=True)
            print("Writing HTML coverage report to %s/ ... " % html_dir, end="")
            sys.stdout.flush()

            # Custom HTML reporter to clean up module names.
            from coverage.html import HtmlReporter

            class CustomHtmlReporter(HtmlReporter):
                def find_code_units(self, morfs):
                    """

                    Parameters
                    ----------
                    morfs :
                    """
                    super(CustomHtmlReporter, self).find_code_units(morfs)
                    for cu in self.code_units:
                        nameparts = cu.name.split(os.sep)
                        if "IPython" not in nameparts:
                            continue
                        ix = nameparts.index("IPython")
                        cu.name = ".".join(nameparts[ix:])

            # Reimplement the html_report method with our custom reporter
            cov.get_data()
            cov.config.from_args(
                omit="*{0}tests{0}*".format(os.sep),
                html_dir=html_dir,
                html_title="IPython test coverage",
            )
            reporter = CustomHtmlReporter(cov, cov.config)
            reporter.report(None)
            print("done.")

        # Coverage XML report
        elif options.coverage == "xml":
            try:
                cov.xml_report(outfile="ipy_coverage.xml")
            except CoverageException as e:
                print(
                    "Generating coverage report failed. Are you running javascript tests only?"
                )
                import traceback

                traceback.print_exc()

    if failed:
        # Ensure that our exit code indicates failure
        sys.exit(1)


def default_options():
    """Get an argparse Namespace object with the default arguments, to pass to
    :func:`run_iptestall`.
    """
    options = argparser.parse_args([])
    options.extra_args = []
    return options


def parse_testing_arguments():
    argparser = argparse.ArgumentParser(description="Run IPython test suite")
    argparser.add_argument(
        "testgroups",
        nargs="*",
        help="Run specified groups of tests. If omitted, run " "all tests.",
    )
    argparser.add_argument(
        "--all", action="store_true", help="Include slow tests not run by default."
    )
    argparser.add_argument(
        "-j",
        "--fast",
        nargs="?",
        const=None,
        default=1,
        type=int,
        help="Run test sections in parallel. This starts as many "
        "processes as you have cores, or you can specify a number.",
    )
    argparser.add_argument(
        "--xunit", action="store_true", help="Produce Xunit XML results"
    )
    argparser.add_argument(
        "--coverage",
        nargs="?",
        const=True,
        default=False,
        help="Measure test coverage. Specify 'html' or " "'xml' to get reports.",
    )
    argparser.add_argument(
        "--subproc-streams",
        default="capture",
        help="What to do with stdout/stderr from subprocesses. "
        "'capture' (default), 'show' and 'discard' are the options.",
    )

    return argparser


def main():
    """Moved this out of the function and now it's harmless :D.

    # iptest doesn't work correctly if the working directory is the
    # root of the IPython source tree. Tell the user to avoid
    # frustration.
    if os.path.exists(os.path.join(os.getcwd(),
                                   'IPython', 'testing', '__main__.py')):
        print("Don't run iptest from the IPython source directory",
              file=sys.stderr)
        sys.exit(1)

    # Arguments after -- should be passed through to nose. Argparse treats
    # everything after -- as regular positional arguments, so we separate them
    # first.

    """
    argparser = parse_testing_arguments()
    try:
        ix = sys.argv.index("--")
    except ValueError:
        to_parse = sys.argv[1:]
        extra_args = []
    else:
        to_parse = sys.argv[1:ix]
        extra_args = sys.argv[ix + 1 :]

    options = argparser.parse_args(to_parse)
    options.extra_args = extra_args

    run_iptestall(options)


if __name__ == "__main__":
    main()
