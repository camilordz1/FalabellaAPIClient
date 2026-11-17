import re

import pytest
import requests
import responses

from falabella_sdk import FalabellaAPIError

BASE_URL = re.compile(r"https://sellercenter-api\.falabella\.com")

ERROR_RESPONSE = {
    "ErrorResponse": {
        "Head": {
            "RequestAction": "ProductUpdate",
            "ErrorType": "Sender",
            "ErrorCode": "5",
            "ErrorMessage": "E005: Invalid Request Format",
        },
        "Body": {
            "ErrorDetail": [
                {
                    "Field": "Price",
                    "Message": "Field must contain a valid number",
                    "Value": "abc",
                    "SellerSku": "TP-1",
                }
            ]
        },
    }
}


@responses.activate
def test_200_with_error_response_raises(client):
    responses.add(responses.POST, url=BASE_URL, json=ERROR_RESPONSE, status=200)

    with pytest.raises(FalabellaAPIError) as exc_info:
        client.query("POST", params={"Action": "ProductUpdate"}, payload="<Request/>")

    exc = exc_info.value
    assert str(exc) == "E005: Invalid Request Format"
    assert exc.error_code == "5"
    assert exc.error_type == "Sender"
    assert exc.action == "ProductUpdate"
    assert exc.status_code == 200
    assert len(exc.details) == 1
    assert exc.details[0]["Field"] == "Price"


@responses.activate
def test_error_detail_single_dict_is_normalized_to_list(client):
    body = {
        "ErrorResponse": {
            "Head": {"ErrorCode": "5", "ErrorMessage": "Invalid Request Format"},
            "Body": {
                "ErrorDetail": {
                    "Field": "Price",
                    "Message": "Field must contain a valid number",
                }
            },
        }
    }
    responses.add(responses.GET, url=BASE_URL, json=body, status=200)

    with pytest.raises(FalabellaAPIError) as exc_info:
        client.query("GET", params={"Action": "GetProducts"})

    assert isinstance(exc_info.value.details, list)
    assert len(exc_info.value.details) == 1
    assert exc_info.value.details[0]["Field"] == "Price"


@responses.activate
def test_error_response_without_body_has_empty_details(client):
    body = {
        "ErrorResponse": {
            "Head": {"ErrorCode": "5", "ErrorMessage": "Invalid Request Format"}
        }
    }
    responses.add(responses.GET, url=BASE_URL, json=body, status=200)

    with pytest.raises(FalabellaAPIError) as exc_info:
        client.query("GET", params={"Action": "GetProducts"})

    assert exc_info.value.details == []


@responses.activate
def test_200_success_response_is_returned_unchanged(client):
    body = {
        "SuccessResponse": {
            "Head": {"RequestId": "req-1"},
            "Body": {"Products": {"Product": [{"SellerSku": "TP-1"}]}},
        }
    }
    responses.add(responses.GET, url=BASE_URL, json=body, status=200)

    result = client.query("GET", params={"Action": "GetProducts"})

    assert result == body


@responses.activate
def test_200_empty_body_returns_empty_dict(client):
    responses.add(responses.GET, url=BASE_URL, body="", status=200)

    result = client.query("GET", params={"Action": "GetProducts"})

    assert result == {}


@responses.activate
def test_400_with_error_response_raises_with_code(client):
    responses.add(responses.POST, url=BASE_URL, json=ERROR_RESPONSE, status=400)

    with pytest.raises(FalabellaAPIError) as exc_info:
        client.query("POST", params={"Action": "ProductUpdate"}, payload="<Request/>")

    exc = exc_info.value
    assert exc.error_code == "5"
    assert exc.error_type == "Sender"
    assert exc.action == "ProductUpdate"
    assert exc.status_code == 400
    assert str(exc) == "E005: Invalid Request Format"


@responses.activate
def test_500_non_json_body_uses_text_as_message(client):
    responses.add(
        responses.GET,
        url=BASE_URL,
        body="Internal Server Error",
        status=500,
        content_type="text/plain",
    )

    with pytest.raises(FalabellaAPIError) as exc_info:
        client.query("GET", params={"Action": "GetProducts"})

    assert str(exc_info.value) == "Internal Server Error"
    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code is None
    assert exc_info.value.details == []


@responses.activate
def test_network_error_raises_with_cause(client):
    responses.add(
        responses.GET,
        url=BASE_URL,
        body=requests.ConnectionError("connection refused"),
    )

    with pytest.raises(FalabellaAPIError) as exc_info:
        client.query("GET", params={"Action": "GetProducts"})

    assert isinstance(exc_info.value.__cause__, requests.ConnectionError)


def test_error_constructor_is_backward_compatible():
    exc = FalabellaAPIError("m", 400, "b")

    assert str(exc) == "m"
    assert exc.status_code == 400
    assert exc.response_body == "b"
