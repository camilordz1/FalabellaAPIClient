import pytest

from falabella_sdk import FalabellaClient


@pytest.fixture
def client():
    client = FalabellaClient(user="seller@example.com", key="test-api-key")
    # Keep retry paths exercised without sleeping for real in tests.
    client._sleep = lambda _seconds: None
    return client
