import responses

from tests.helpers import RESPONSE, add, params, sent_params


@responses.activate
def test_get_sends_default_limit(client):
    add(responses.GET)

    assert client.products.get() == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetProducts", Limit="1000")


@responses.activate
def test_get_merges_filters_and_custom_limit(client):
    add(responses.GET)

    client.products.get(limit=10, SkuSellerList='["TP-1"]', Search="red shoe")

    assert sent_params(responses.calls[0]) == params(
        "GetProducts",
        Limit="10",
        SkuSellerList='["TP-1"]',
        Search="red shoe",
    )


@responses.activate
def test_create_sends_post_xml_body(client):
    add(responses.POST)
    payload = "<Request><Product><SellerSku>TP-1</SellerSku></Product></Request>"

    assert client.products.create(payload) == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "POST"
    assert sent_params(call) == params("ProductCreate")
    assert call.request.body == payload.encode("utf-8")


@responses.activate
def test_update_sends_post_xml_body(client):
    add(responses.POST)
    payload = "<Request><Product><SellerSku>TP-1</SellerSku></Product></Request>"

    assert client.products.update(payload) == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "POST"
    assert sent_params(call) == params("ProductUpdate")
    assert call.request.body == payload.encode("utf-8")


@responses.activate
def test_remove_sends_post_xml_body(client):
    add(responses.POST)
    payload = "<Request><Product><SellerSku>TP-1</SellerSku></Product></Request>"

    assert client.products.remove(payload) == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "POST"
    assert sent_params(call) == params("ProductRemove")
    assert call.request.body == payload.encode("utf-8")


@responses.activate
def test_brands_sends_get(client):
    add(responses.GET)

    assert client.products.brands() == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetBrands")
    assert call.request.body is None


@responses.activate
def test_get_category_tree_sends_get(client):
    add(responses.GET)

    assert client.products.get_category_tree() == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetCategoryTree")


@responses.activate
def test_get_category_attributes_sends_primary_category(client):
    add(responses.GET)

    assert client.products.get_category_attributes(1234) == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetCategoryAttributes", PrimaryCategory="1234")
