# Yeah so this just raised so many MultipleInstanceErrors that these tests don't run.
import pytest
from traitlets.config import MultipleInstanceError


@pytest.fixture
def start_test_shell():
    """Will this fix it?"""
    return None
