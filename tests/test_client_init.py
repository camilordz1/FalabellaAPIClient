import pytest

import falabella_sdk
from falabella_sdk import FalabellaClient, Products


def test_base_url_is_falabella():
    client = FalabellaClient("u", "k", seller_id="ABC123")

    assert client.url == "https://sellercenter-api.falabella.com"


@pytest.mark.parametrize("options", [{"service": "linio"}, {"country": "cl"}])
def test_service_and_country_are_rejected(options):
    with pytest.raises(TypeError):
        FalabellaClient("u", "k", seller_id="ABC123", **options)


def test_positional_third_argument_is_rejected():
    with pytest.raises(TypeError):
        FalabellaClient("u", "k", "falabella")


def test_legacy_names_are_not_exported():
    assert not hasattr(falabella_sdk, "Session")
    assert not hasattr(falabella_sdk, "Service")
    assert "Session" not in falabella_sdk.__all__
    assert "Service" not in falabella_sdk.__all__


def test_resource_requires_client():
    with pytest.raises(TypeError):
        Products()
