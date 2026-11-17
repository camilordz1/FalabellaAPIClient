import copy

import pytest

from falabella_sdk.responses import FalabellaResponse, as_list, get_list, unwrap

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


@pytest.mark.parametrize("body_value", [None, ""])
def test_empty_body_becomes_empty_dict(body_value):
    raw = {"SuccessResponse": {"Head": {"RequestAction": "GetOrders"}, "Body": body_value}}

    assert unwrap(raw).body == {}


@pytest.mark.parametrize("body_value", [[], "text", [{"SellerSku": "TP-1"}]])
def test_non_dict_body_is_kept(body_value):
    raw = {"SuccessResponse": {"Head": {"RequestAction": "GetOrders"}, "Body": body_value}}

    response = unwrap(raw)

    assert response.body is body_value


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

    with pytest.raises(ValueError, match="ErrorResponse"):
        unwrap(raw)


@pytest.mark.parametrize("success_value", ["x", []])
def test_non_dict_success_response_falls_back_to_raw(success_value):
    raw = {"SuccessResponse": success_value}

    response = unwrap(raw)

    assert response.head == {}
    assert response.body is raw


@pytest.mark.parametrize("value", [None, ""])
def test_as_list_returns_empty_list_for_none_and_empty_string(value):
    assert as_list(value) == []


def test_as_list_wraps_dict_keeping_identity():
    value = {"SellerSku": "TP-1"}

    result = as_list(value)

    assert result == [value]
    assert result[0] is value


def test_as_list_returns_same_list():
    value = [{"SellerSku": "A"}, {"SellerSku": "B"}]

    assert as_list(value) is value


@pytest.mark.parametrize("value, expected", [("x", ["x"]), (5, [5])])
def test_as_list_wraps_other_values(value, expected):
    assert as_list(value) == expected


ONE_PRODUCT_BODY = {"Products": {"Product": {"SellerSku": "A"}}}
TWO_PRODUCTS_BODY = {
    "Products": {"Product": [{"SellerSku": "A"}, {"SellerSku": "B"}]}
}
EMPTY_PRODUCTS_BODY = {"Products": {"Product": ""}}


def test_get_list_wraps_single_item_dict():
    assert get_list(ONE_PRODUCT_BODY, "Products", "Product") == [{"SellerSku": "A"}]


def test_get_list_returns_collection_list():
    result = get_list(TWO_PRODUCTS_BODY, "Products", "Product")

    assert result == [{"SellerSku": "A"}, {"SellerSku": "B"}]
    assert result is TWO_PRODUCTS_BODY["Products"]["Product"]


def test_get_list_returns_empty_list_for_empty_string_collection():
    assert get_list(EMPTY_PRODUCTS_BODY, "Products", "Product") == []


def test_get_list_returns_empty_list_for_missing_key():
    assert get_list({"Products": {}}, "Products", "Product") == []


@pytest.mark.parametrize("intermediate", ["", None, [{"Product": {"SellerSku": "A"}}]])
def test_get_list_returns_empty_list_for_non_dict_intermediate(intermediate):
    assert get_list({"Products": intermediate}, "Products", "Product") == []


def test_get_list_requires_a_path():
    with pytest.raises(TypeError):
        get_list({"Products": {}})


def test_get_list_does_not_mutate_container():
    original = copy.deepcopy(TWO_PRODUCTS_BODY)

    get_list(TWO_PRODUCTS_BODY, "Products", "Product")

    assert TWO_PRODUCTS_BODY == original


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
