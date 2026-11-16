import pytest

from FalabellaAPIClient import FalabellaClient


@pytest.fixture
def client():
    return FalabellaClient(user="seller@example.com", key="test-api-key")
