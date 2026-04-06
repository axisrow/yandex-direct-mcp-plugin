import pytest


@pytest.fixture
def token():
    """Test OAuth token."""
    return "test-access-token"
