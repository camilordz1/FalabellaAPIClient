import copy

import pytest

from falabella_sdk.responses import FalabellaResponse, unwrap

PRODUCTS_RESPONSE = {
    "SuccessResponse": {
        "Head": {
            "RequestId": "",
            "RequestAction": "GetProducts",
            "ResponseType": "Products",
            "Timestamp": "2026-11-17T01:32:53-0300",
        },
        "Body": {"Products": {"Product": {"SellerSku": "TP-1"}}},
    }
}

EMPTY_ORDERS_RESPONSE = {
    "SuccessResponse": {
        "Head": {
            "RequestId": "",
            "RequestAction": "GetOrders",
            "ResponseType": "Orders",
            "Timestamp": "2026-11-17T04:32:55Z",
            "TotalCount": "0",
        },
        "Body": {"Orders": ""},
    }
}


def test_unwrap_extracts_head_and_body_and_keeps_raw():
    response = unwrap(PRODUCTS_RESPONSE)

    assert isinstance(response, FalabellaResponse)
    assert response.head == PRODUCTS_RESPONSE["SuccessResponse"]["Head"]
    assert response.body == {"Products": {"Product": {"SellerSku": "TP-1"}}}
    assert response.raw is PRODUCTS_RESPONSE


@pytest.mark.parametrize("body_value", [None, "", [], "text"])
def test_body_that_is_not_a_dict_becomes_empty_dict(body_value):
    raw = {"SuccessResponse": {"Head": {"RequestAction": "GetOrders"}, "Body": body_value}}

    assert unwrap(raw).body == {}


def test_missing_body_becomes_empty_dict():
    raw = {"SuccessResponse": {"Head": {"RequestAction": "GetOrders"}}}

    assert unwrap(raw).body == {}


@pytest.mark.parametrize("head_value", [None, "", [], "text"])
def test_head_that_is_not_a_dict_becomes_empty_dict(head_value):
    raw = {"SuccessResponse": {"Head": head_value, "Body": {"Orders": ""}}}

    assert unwrap(raw).head == {}


def test_request_id_returns_value_when_present():
    raw = {"SuccessResponse": {"Head": {"RequestId": "b6dc5a1c-1234"}, "Body": {}}}

    assert unwrap(raw).request_id == "b6dc5a1c-1234"


@pytest.mark.parametrize("head", [{"RequestId": ""}, {}])
def test_request_id_is_none_when_empty_or_missing(head):
    assert unwrap({"SuccessResponse": {"Head": head, "Body": {}}}).request_id is None


def test_request_action_and_response_type():
    response = unwrap(EMPTY_ORDERS_RESPONSE)

    assert response.request_action == "GetOrders"
    assert response.response_type == "Orders"


def test_request_action_and_response_type_are_none_when_missing():
    response = unwrap({"SuccessResponse": {"Head": {}, "Body": {}}})

    assert response.request_action is None
    assert response.response_type is None


@pytest.mark.parametrize(
    "head, expected",
    [
        ({"TotalCount": "0"}, 0),
        ({"TotalCount": "12"}, 12),
        ({"TotalCount": 7}, 7),
        ({}, None),
        ({"TotalCount": ""}, None),
        ({"TotalCount": "abc"}, None),
        ({"TotalCount": True}, None),
    ],
)
def test_total_count(head, expected):
    assert unwrap({"SuccessResponse": {"Head": head, "Body": {}}}).total_count == expected


def test_error_response_raises_value_error():
    raw = {"ErrorResponse": {"Head": {"ErrorCode": "5", "ErrorMessage": "Invalid"}}}

    with pytest.raises(ValueError):
        unwrap(raw)


@pytest.mark.parametrize("raw", [{}, {"response_text": "x"}, [], None])
def test_non_envelope_values_are_returned_as_body(raw):
    response = unwrap(raw)

    assert response.head == {}
    assert response.body is raw
    assert response.raw is raw


def test_input_is_not_mutated():
    original = copy.deepcopy(PRODUCTS_RESPONSE)

    response = unwrap(PRODUCTS_RESPONSE)

    assert PRODUCTS_RESPONSE == original
    assert response.raw is PRODUCTS_RESPONSE
