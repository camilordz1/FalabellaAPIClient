import re
from urllib.parse import parse_qs, urlparse

import responses

BASE_URL = re.compile(r"https://sellercenter-api\.falabella\.com")
RESPONSE = {"SuccessResponse": {"Head": {"RequestId": "req-1"}, "Body": {}}}


def add(method, body=RESPONSE):
    """Register the mocked Falabella endpoint for one call."""
    responses.add(method, BASE_URL, json=body, status=200)


def sent_params(call):
    """First value of every query param, excluding signature metadata."""
    query = parse_qs(urlparse(call.request.url).query)
    return {
        key: values[0]
        for key, values in query.items()
        if key not in ("Signature", "Timestamp")
    }


def params(action, **extra):
    return {
        "Action": action,
        "UserID": "seller@example.com",
        "Version": "1.0",
        "Format": "JSON",
        **extra,
    }
