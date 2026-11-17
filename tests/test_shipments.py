import responses

from falabella_sdk import FalabellaResponse
from tests.helpers import RESPONSE, add, params, sent_params


@responses.activate
def test_get_providers_sends_get(client):
    add(responses.GET)

    result = client.shipments.get_providers()

    assert isinstance(result, FalabellaResponse)
    assert result.raw == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetShipmentProviders")
    assert call.request.body is None


@responses.activate
def test_get_document_serializes_list_and_default_type(client):
    add(responses.GET)

    result = client.shipments.get_document([1, 2])

    assert isinstance(result, FalabellaResponse)
    assert result.raw == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params(
        "GetDocument", OrderItemIds="[1, 2]", DocumentType="shippingLabel"
    )


@responses.activate
def test_get_document_accepts_serialized_string_and_custom_type(client):
    add(responses.GET)

    client.shipments.get_document("[1, 2]", document_type="invoice")

    assert sent_params(responses.calls[0]) == params(
        "GetDocument", OrderItemIds="[1, 2]", DocumentType="invoice"
    )


def body(collection, value):
    return {"SuccessResponse": {"Head": {"RequestId": "req-1"}, "Body": {collection: value}}}


@responses.activate
def test_get_providers_returns_single_provider_as_items(client):
    add(responses.GET, body("ShipmentProviders", {"ShipmentProvider": {"Id": 1}}))

    assert client.shipments.get_providers().items == [{"Id": 1}]


@responses.activate
def test_get_providers_returns_multiple_providers_as_items(client):
    add(
        responses.GET,
        body("ShipmentProviders", {"ShipmentProvider": [{"Id": 1}, {"Id": 2}]}),
    )

    assert len(client.shipments.get_providers().items) == 2
