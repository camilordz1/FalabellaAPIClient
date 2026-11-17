import hashlib
import hmac
import re
from urllib.parse import quote, urlencode

import pytest
from freezegun import freeze_time

FROZEN_TIME = "2026-01-15T10:30:00Z"
GOLDEN_SIGNATURE = "ab590d19c3315c1e93e364e0b5055d98b732b0c30021f0e5fa6fb3f055a9b024"


def _reference_signature(params, key):
    """Compute the HMAC-SHA256 signature over the RFC 3986 encoded, sorted params."""
    sorted_items = sorted(params.items())
    encoded = urlencode(sorted_items, quote_via=quote, safe="").encode("utf-8")
    return hmac.new(key.encode("utf-8"), encoded, hashlib.sha256).hexdigest()


@freeze_time(FROZEN_TIME)
def test_signature_includes_base_params(client):
    result = client.signature()

    assert result["UserID"] == "seller@example.com"
    assert result["Version"] == "1.0"
    assert result["Format"] == "JSON"
    assert result["Timestamp"] == FROZEN_TIME
    assert "Signature" in result


@freeze_time(FROZEN_TIME)
def test_timestamp_is_utc_iso8601_without_microseconds(client):
    timestamp = client.signature()["Timestamp"]

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", timestamp)


@freeze_time(FROZEN_TIME)
def test_signature_matches_reference_hmac(client):
    result = client.signature()

    expected_params = {
        "UserID": "seller@example.com",
        "Version": "1.0",
        "Format": "JSON",
        "Timestamp": FROZEN_TIME,
    }
    expected = _reference_signature(expected_params, "test-api-key")

    assert result["Signature"] == expected
    assert result["Signature"] == GOLDEN_SIGNATURE


@freeze_time(FROZEN_TIME)
def test_extra_params_are_signed(client):
    base_signature = client.signature()["Signature"]

    result = client.signature({"Action": "GetProducts", "Limit": 10})

    assert result["Action"] == "GetProducts"
    assert result["Limit"] == 10
    assert result["Signature"] != base_signature


@freeze_time(FROZEN_TIME)
def test_does_not_mutate_input_params(client):
    params = {"Action": "GetProducts", "Limit": 10}
    original = dict(params)

    client.signature(params)

    assert params == original


def _signed_string(extra):
    items = sorted(
        {
            "UserID": "seller@example.com",
            "Version": "1.0",
            "Format": "JSON",
            "Timestamp": FROZEN_TIME,
            **extra,
        }.items()
    )
    return urlencode(items, quote_via=quote, safe="")


@pytest.mark.parametrize(
    ("value", "encoded"),
    [
        ("red shoe", "red%20shoe"),
        ("ñandú", "%C3%B1and%C3%BA"),
        ("12v/110v", "12v%2F110v"),
        ("a+b", "a%2Bb"),
        ("x~y-z_w.v", "x~y-z_w.v"),
    ],
)
@freeze_time(FROZEN_TIME)
def test_signature_uses_rfc3986_percent_encoding(client, value, encoded):
    """Falabella signs like PHP rawurlencode: %20 for spaces and %2F for slashes.

    Verified against the real API (F0-02b): '+' for spaces or a bare '/' gives E007
    "Signature mismatch".
    """
    signed = _signed_string({"Search": value})
    assert f"Search={encoded}&" in signed

    expected = hmac.new(b"test-api-key", signed.encode("utf-8"), hashlib.sha256).hexdigest()

    assert client.signature({"Search": value})["Signature"] == expected
