import re
from unittest.mock import patch

import pytest
import requests
import responses

from FalabellaAPIClient import FalabellaAPIError, FalabellaClient

URL = re.compile(r"https://sellercenter-api\.falabella\.com")
OK = {"SuccessResponse": {"Head": {"RequestId": "req-1"}, "Body": {}}}
XML = "<Request><Name>Camión ñandú — 5</Name></Request>"


def make(**options):
    client = FalabellaClient(user="seller@example.com", key="test-api-key", **options)
    sleeps = []
    client._sleep = sleeps.append
    return client, sleeps


def err(code="429", message="Too Many"):
    return {"ErrorResponse": {"Head": {"ErrorCode": code, "ErrorMessage": message}}}


def add(method, status=200, body=None, headers=None):
    responses.add(method, URL, json=OK if body is None else body, status=status, headers=headers)


def get(client):
    return client.query("GET", {"Action": "GetProducts"})


@responses.activate
def test_timeout_is_passed_to_request():
    add(responses.GET)
    for options, expected in (({}, 30.0), ({"timeout": 5.5}, 5.5)):
        client, _ = make(**options)
        with patch.object(client.session, "request", wraps=client.session.request) as spy:
            get(client)
        assert spy.call_args.kwargs["timeout"] == expected


@responses.activate
def test_timeout_error_raises_falabella_error_with_cause():
    responses.add(responses.GET, URL, body=requests.Timeout("timed out"))
    client, sleeps = make(max_retries=0)
    with pytest.raises(FalabellaAPIError) as exc_info:
        get(client)
    assert isinstance(exc_info.value.__cause__, requests.Timeout)
    assert sleeps == []


@responses.activate
def test_str_payload_is_utf8_encoded_with_xml_content_type(client):
    add(responses.POST)
    client.query("POST", {"Action": "ProductUpdate"}, payload=XML)
    request = responses.calls[0].request
    assert request.body == XML.encode("utf-8")
    assert request.headers["Content-Type"] == "application/xml; charset=utf-8"


@responses.activate
def test_caller_content_type_overrides_default(client):
    add(responses.POST)
    client.query("POST", {"Action": "ProductUpdate"}, payload=XML,
                 headers={"Content-Type": "text/xml"})
    request = responses.calls[0].request
    assert request.body == XML.encode("utf-8")
    assert request.headers["Content-Type"] == "text/xml"


@responses.activate
def test_get_without_payload_has_no_content_type(client):
    add(responses.GET)
    get(client)
    assert "Content-Type" not in responses.calls[0].request.headers


@responses.activate
def test_get_retries_on_429_then_succeeds():
    add(responses.GET, 429, err())
    add(responses.GET, 429, err())
    add(responses.GET)
    client, sleeps = make(backoff_factor=1.0)
    assert get(client) == OK
    assert (len(responses.calls), sleeps) == (3, [1.0, 2.0])


@responses.activate
def test_retry_after_header_is_respected():
    add(responses.GET, 429, err(), headers={"Retry-After": "7"})
    add(responses.GET)
    client, sleeps = make()
    get(client)
    assert sleeps == [7.0]


@responses.activate
def test_post_retries_on_429():
    add(responses.POST, 429, err())
    add(responses.POST)
    client, _ = make()
    assert client.query("POST", {"Action": "ProductUpdate"}, payload=XML) == OK
    assert len(responses.calls) == 2


@responses.activate
def test_post_does_not_retry_on_500(client):
    add(responses.POST, 500, err("5", "Server Error"))
    with pytest.raises(FalabellaAPIError) as exc_info:
        client.query("POST", {"Action": "ProductUpdate"}, payload=XML)
    assert (exc_info.value.status_code, len(responses.calls)) == (500, 1)


@responses.activate
def test_get_retries_on_500_then_succeeds():
    add(responses.GET, 500, err("5", "Server Error"))
    add(responses.GET)
    client, _ = make()
    assert (get(client), len(responses.calls)) == (OK, 2)


@responses.activate
def test_post_does_not_retry_on_connection_error(client):
    responses.add(responses.POST, URL, body=requests.ConnectionError("refused"))
    with pytest.raises(FalabellaAPIError) as exc_info:
        client.query("POST", {"Action": "ProductUpdate"}, payload=XML)
    assert isinstance(exc_info.value.__cause__, requests.ConnectionError)
    assert len(responses.calls) == 1


@responses.activate
def test_get_retries_on_connection_error_then_succeeds():
    responses.add(responses.GET, URL, body=requests.ConnectionError("refused"))
    add(responses.GET)
    client, sleeps = make()
    assert (get(client), len(responses.calls), sleeps) == (OK, 2, [1.0])


@responses.activate
def test_error_code_429_in_body_is_retried():
    add(responses.GET, 200, err())
    add(responses.GET)
    client, _ = make()
    assert (get(client), len(responses.calls)) == (OK, 2)


@responses.activate
def test_error_code_429_as_int_is_retried():
    add(responses.GET, 200, err(429))
    add(responses.GET)
    client, _ = make()
    assert (get(client), len(responses.calls)) == (OK, 2)


@responses.activate
def test_retries_exhausted_raises_last_error():
    for _ in range(4):
        add(responses.GET, 429, err())
    client, sleeps = make()
    with pytest.raises(FalabellaAPIError) as exc_info:
        get(client)
    assert (exc_info.value.status_code, len(responses.calls), sleeps) == (429, 4, [1.0, 2.0, 4.0])


@responses.activate
def test_max_retries_zero_disables_retry():
    add(responses.GET, 429, err())
    add(responses.GET)
    client, sleeps = make(max_retries=0)
    with pytest.raises(FalabellaAPIError) as exc_info:
        get(client)
    assert (exc_info.value.status_code, len(responses.calls), sleeps) == (429, 1, [])


@responses.activate
def test_each_attempt_is_re_signed():
    add(responses.GET, 429, err())
    add(responses.GET)
    client, _ = make()
    with patch.object(client, "signature", wraps=client.signature) as spy:
        get(client)
    assert spy.call_count == 2


@responses.activate
def test_non_retryable_error_is_not_retried(client):
    add(responses.GET, 200, err("5", "Invalid Format"))
    with pytest.raises(FalabellaAPIError) as exc_info:
        get(client)
    assert (exc_info.value.error_code, len(responses.calls)) == ("5", 1)


@responses.activate
def test_delay_is_capped_at_60_seconds():
    add(responses.GET, 429, err(), headers={"Retry-After": "600"})
    add(responses.GET)
    client, sleeps = make()
    get(client)
    assert sleeps == [60.0]
