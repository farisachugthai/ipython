"""This was in the init but it caused nose to be a hard dependency."""
from nose.tools.nontrivial import nottest


@nottest
def test(**kwargs):
    """Run the entire IPython test suite.

    Any of the options for run_iptestall() may be passed as keyword arguments.

    For example::

        IPython.test(testgroups=['lib', 'config', 'utils'], fast=2)

    will run those three sections of the test suite, using two processes.
    """

    # Do the import internally, so that this function doesn't increase total
    # import time
    from .iptestcontroller import run_iptestall, default_options
    options = default_options()
    for name, val in kwargs.items():
        setattr(options, name, val)
    run_iptestall(options)


if __name__ == '__main__':
    from IPython.testing import iptestcontroller
    iptestcontroller.main()
