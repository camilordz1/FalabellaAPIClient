import responses

from tests.helpers import RESPONSE, add, params, sent_params


@responses.activate
def test_get_sends_get(client):
    add(responses.GET)

    assert client.seller.get() == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetSellerByUser")
    assert call.request.body is None
