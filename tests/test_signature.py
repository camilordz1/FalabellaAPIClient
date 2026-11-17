import hashlib
import hmac
import re
from urllib.parse import quote, urlencode

from freezegun import freeze_time

FROZEN_TIME = "2026-01-15T10:30:00Z"
GOLDEN_SIGNATURE = "ab590d19c3315c1e93e364e0b5055d98b732b0c30021f0e5fa6fb3f055a9b024"


def _reference_signature(params, key):
    """Compute the HMAC-SHA256 signature the way the current algorithm does."""
    sorted_items = sorted(params.items())
    encoded = urlencode(sorted_items).encode("utf-8")
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


@freeze_time(FROZEN_TIME)
def test_space_encoding_current_behavior(client):
    params = {"Search": "red shoe"}
    signature = client.signature(params)["Signature"]

    signed_items = sorted(
        {
            "UserID": "seller@example.com",
            "Version": "1.0",
            "Format": "JSON",
            "Timestamp": FROZEN_TIME,
            "Search": "red shoe",
        }.items()
    )
    plus_encoded = urlencode(signed_items).encode("utf-8")
    percent_encoded = urlencode(signed_items, quote_via=quote).encode("utf-8")

    assert signature == hmac.new(
        b"test-api-key", plus_encoded, hashlib.sha256
    ).hexdigest()
    assert signature != hmac.new(
        b"test-api-key", percent_encoded, hashlib.sha256
    ).hexdigest()
    # Docs are inconsistent (PHP sample: rawurlencode %20; Python sample: +). Pending real-API check F0-02b.
