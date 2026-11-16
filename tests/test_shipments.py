import responses

from tests.helpers import RESPONSE, add, params, sent_params


@responses.activate
def test_get_providers_sends_get(client):
    add(responses.GET)

    assert client.shipments.get_providers() == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetShipmentProviders")
    assert call.request.body is None


@responses.activate
def test_get_document_serializes_list_and_default_type(client):
    add(responses.GET)

    assert client.shipments.get_document([1, 2]) == RESPONSE

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
