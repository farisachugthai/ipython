try:
    from numpy.testing import KnownFailure, knownfailureif
except ImportError:
    from ._decorators import knownfailureif

    try:
        from ._numpy_testing_noseclasses import KnownFailure
    except ImportError:
        pass


def pytest_check():
    try:
        import pytest
    except ImportError:
        return
    else:
        return True


if pytest_check() is not None:

    from pytest import mark
    # TODO: check that this worked
    KnownFailure = mark.xfail
    # knownfailureif = pytest.importorskip('numpy.testing.knownfailureif')

    # TODO:

