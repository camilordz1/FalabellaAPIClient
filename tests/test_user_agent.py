import platform
import re

import pytest
import responses

from FalabellaAPIClient import FalabellaClient

URL = re.compile(r"https://sellercenter-api\.falabella\.com")
OK = {"SuccessResponse": {"Head": {"RequestId": "req-1"}, "Body": {}}}


def make(**options):
    return FalabellaClient(user="seller@example.com", key="test-api-key", **options)


@responses.activate
def test_user_agent_header_format():
    responses.add(responses.GET, URL, json=OK)
    client = make(seller_id="ABC123")

    client.query("GET", {"Action": "GetProducts"})

    expected = f"ABC123/Python/{platform.python_version()}/PROPIA/FACO"
    assert responses.calls[0].request.headers["User-Agent"] == expected


@responses.activate
def test_business_unit_is_normalized_to_upper_case():
    responses.add(responses.GET, URL, json=OK)
    client = make(seller_id="ABC123", business_unit="facl")

    client.query("GET", {"Action": "GetProducts"})

    user_agent = responses.calls[0].request.headers["User-Agent"]
    assert user_agent.endswith("/FACL")
    assert client.business_unit == "FACL"


def test_invalid_business_unit_raises():
    with pytest.raises(ValueError):
        make(seller_id="ABC123", business_unit="FACX")


def test_seller_id_with_slash_raises():
    with pytest.raises(ValueError):
        make(seller_id="AB/C")


def test_empty_integration_type_raises():
    with pytest.raises(ValueError):
        make(seller_id="ABC123", integration_type="")


@responses.activate
def test_custom_integration_type():
    responses.add(responses.GET, URL, json=OK)
    client = make(seller_id="ABC123", integration_type="MYINTEGRATOR")

    client.query("GET", {"Action": "GetProducts"})

    assert responses.calls[0].request.headers["User-Agent"].startswith(
        "ABC123/Python/"
    )
    assert responses.calls[0].request.headers["User-Agent"].endswith(
        "/MYINTEGRATOR/FACO"
    )


@responses.activate
def test_missing_seller_id_warns_and_sends_no_user_agent_override():
    responses.add(responses.GET, URL, json=OK)
    with pytest.warns(UserWarning):
        client = make()

    client.query("GET", {"Action": "GetProducts"})

    user_agent = responses.calls[0].request.headers["User-Agent"]
    assert user_agent.startswith("python-requests/")


@responses.activate
def test_caller_user_agent_header_wins():
    responses.add(responses.GET, URL, json=OK)
    client = make(seller_id="ABC123")

    client.query(
        "GET", {"Action": "GetProducts"}, headers={"User-Agent": "custom/1.0"}
    )

    assert responses.calls[0].request.headers["User-Agent"] == "custom/1.0"
