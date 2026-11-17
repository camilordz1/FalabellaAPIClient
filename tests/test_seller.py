import responses

from falabella_sdk import FalabellaResponse
from tests.helpers import RESPONSE, add, params, sent_params


@responses.activate
def test_get_sends_get(client):
    add(responses.GET)

    result = client.seller.get()

    assert isinstance(result, FalabellaResponse)
    assert result.raw == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetSellerByUser")
    assert call.request.body is None
