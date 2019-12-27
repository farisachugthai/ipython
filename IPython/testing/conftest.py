# Yeah so this just raised so many MultipleInstanceErrors that these tests don't run.
from traitlets.config import MultipleInstanceError
import pytest


@pytest.fixture
def start_test_shell():
    """Will this fix it?"""
    return None
