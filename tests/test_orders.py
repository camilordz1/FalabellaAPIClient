import pytest
import responses

from tests.helpers import RESPONSE, add, params, sent_params


@responses.activate
def test_list_sends_get_with_kwargs_filters(client):
    add(responses.GET)

    assert client.orders.list(Limit=10, Country="CO") == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetOrders", Limit="10", Country="CO")


@responses.activate
def test_get_sends_order_id_and_kwargs(client):
    add(responses.GET)

    assert client.orders.get(100513, Country="CO") == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetOrder", OrderId="100513", Country="CO")


@pytest.mark.parametrize("template", ["JSON", "XML"])
@responses.activate
def test_items_sends_order_id_and_template(client, template):
    add(responses.GET)

    client.orders.items(100513, template=template)

    call = responses.calls[0]
    assert call.request.method == "GET"
    expected = params("GetOrderItems", OrderId="100513")
    expected["Format"] = template
    assert sent_params(call) == expected


@responses.activate
def test_multiple_order_items_serializes_list(client):
    add(responses.GET)

    client.orders.multiple_order_items([100513, 100514])

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params(
        "GetMultipleOrderItems", OrderIdList="[100513, 100514]"
    )


@responses.activate
def test_multiple_order_items_accepts_serialized_string(client):
    add(responses.GET)

    client.orders.multiple_order_items("[100513, 100514]")

    assert sent_params(responses.calls[0]) == params(
        "GetMultipleOrderItems", OrderIdList="[100513, 100514]"
    )


@responses.activate
def test_set_status_to_packed_by_marketplace_sends_post(client):
    add(responses.POST)

    assert client.orders.set_status_to_packed_by_marketplace(
        [1, 2], "Falabella", "dropship"
    ) == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "POST"
    assert sent_params(call) == params(
        "SetStatusToPackedByMarketplace",
        OrderItemIds="[1, 2]",
        ShippingProvider="Falabella",
        DeliveryType="dropship",
    )
    assert call.request.body is None


@responses.activate
def test_set_status_to_ready_to_ship_sends_post(client):
    add(responses.POST)

    client.orders.set_status_to_ready_to_ship([1, 2], "Falabella", "TRACK-1", "dropship")

    call = responses.calls[0]
    assert call.request.method == "POST"
    assert sent_params(call) == params(
        "SetStatusToReadyToShip",
        OrderItemIds="[1, 2]",
        ShippingProvider="Falabella",
        TrackingNumber="TRACK-1",
        DeliveryType="dropship",
    )


@responses.activate
def test_set_status_to_shipped_sends_post(client):
    add(responses.POST)

    client.orders.set_status_to_shipped([1, 2], "TRACK-1")

    call = responses.calls[0]
    assert call.request.method == "POST"
    assert sent_params(call) == params(
        "SetStatusToShipped", OrderItemIds="[1, 2]", TrackingNumber="TRACK-1"
    )


@responses.activate
def test_set_status_to_delivered_sends_post(client):
    add(responses.POST)

    client.orders.set_status_to_delivered([1, 2])

    call = responses.calls[0]
    assert call.request.method == "POST"
    assert sent_params(call) == params("SetStatusToDelivered", OrderItemIds="[1, 2]")


@pytest.mark.parametrize("reason_detail, expected", [(None, None), ("address", "address")])
@responses.activate
def test_set_status_to_failed_optional_reason_detail(client, reason_detail, expected):
    add(responses.POST)

    client.orders.set_status_to_failed([1, 2], "no stock", reason_detail=reason_detail)

    call = responses.calls[0]
    assert call.request.method == "POST"
    query = sent_params(call)
    assert query.pop("ReasonDetail", None) == expected
    assert query == params("SetStatusToFailed", OrderItemIds="[1, 2]", Reason="no stock")


@pytest.mark.parametrize("reason_detail, expected", [(None, None), ("address", "address")])
@responses.activate
def test_set_status_to_cancelled_optional_reason_detail(client, reason_detail, expected):
    add(responses.POST)

    client.orders.set_status_to_cancelled([1, 2], "fraud", reason_detail=reason_detail)

    call = responses.calls[0]
    assert call.request.method == "POST"
    query = sent_params(call)
    assert query.pop("ReasonDetail", None) == expected
    assert query == params("SetStatusToCancelled", OrderItemIds="[1, 2]", Reason="fraud")
