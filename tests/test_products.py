import responses

from falabella_sdk import FalabellaResponse
from tests.helpers import RESPONSE, add, params, sent_params


@responses.activate
def test_get_sends_default_limit(client):
    add(responses.GET)

    result = client.products.get()

    assert isinstance(result, FalabellaResponse)
    assert result.raw == RESPONSE

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

    result = client.products.create(payload)

    assert isinstance(result, FalabellaResponse)
    assert result.raw == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "POST"
    assert sent_params(call) == params("ProductCreate")
    assert call.request.body == payload.encode("utf-8")


@responses.activate
def test_update_sends_post_xml_body(client):
    add(responses.POST)
    payload = "<Request><Product><SellerSku>TP-1</SellerSku></Product></Request>"

    result = client.products.update(payload)

    assert isinstance(result, FalabellaResponse)
    assert result.raw == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "POST"
    assert sent_params(call) == params("ProductUpdate")
    assert call.request.body == payload.encode("utf-8")


@responses.activate
def test_remove_sends_post_xml_body(client):
    add(responses.POST)
    payload = "<Request><Product><SellerSku>TP-1</SellerSku></Product></Request>"

    result = client.products.remove(payload)

    assert isinstance(result, FalabellaResponse)
    assert result.raw == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "POST"
    assert sent_params(call) == params("ProductRemove")
    assert call.request.body == payload.encode("utf-8")


@responses.activate
def test_brands_sends_get(client):
    add(responses.GET)

    result = client.products.brands()

    assert isinstance(result, FalabellaResponse)
    assert result.raw == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetBrands")
    assert call.request.body is None


@responses.activate
def test_get_category_tree_sends_get(client):
    add(responses.GET)

    result = client.products.get_category_tree()

    assert isinstance(result, FalabellaResponse)
    assert result.raw == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetCategoryTree")


@responses.activate
def test_get_category_attributes_sends_primary_category(client):
    add(responses.GET)

    result = client.products.get_category_attributes(1234)

    assert isinstance(result, FalabellaResponse)
    assert result.raw == RESPONSE

    call = responses.calls[0]
    assert call.request.method == "GET"
    assert sent_params(call) == params("GetCategoryAttributes", PrimaryCategory="1234")


def body(collection, value):
    return {"SuccessResponse": {"Head": {"RequestId": "req-1"}, "Body": {collection: value}}}


@responses.activate
def test_get_returns_single_product_as_items(client):
    add(responses.GET, body("Products", {"Product": {"SellerSku": "A"}}))

    assert client.products.get().items == [{"SellerSku": "A"}]


@responses.activate
def test_get_returns_multiple_products_as_items(client):
    add(responses.GET, body("Products", {"Product": [{"SellerSku": "A"}, {"SellerSku": "B"}]}))

    assert len(client.products.get().items) == 2


@responses.activate
def test_brands_unwraps_inner_brand_dicts(client):
    add(responses.GET, body("Brands", [{"Brand": {"Id": 1}}, {"Brand": {"Id": 2}}]))

    assert client.products.brands().items == [{"Id": 1}, {"Id": 2}]


@responses.activate
def test_brands_returns_single_inner_brand(client):
    add(responses.GET, body("Brands", {"Brand": {"Id": 1}}))

    assert client.products.brands().items == [{"Id": 1}]


@responses.activate
def test_category_tree_returns_single_category_as_items(client):
    add(responses.GET, body("Categories", {"Category": {"Id": 1}}))

    assert client.products.get_category_tree().items == [{"Id": 1}]


@responses.activate
def test_category_tree_returns_multiple_categories_as_items(client):
    add(responses.GET, body("Categories", {"Category": [{"Id": 1}, {"Id": 2}]}))

    assert len(client.products.get_category_tree().items) == 2


@responses.activate
def test_category_attributes_returns_single_attribute_as_items(client):
    add(responses.GET, body("Attribute", {"Id": "name"}))

    assert client.products.get_category_attributes(1234).items == [{"Id": "name"}]


@responses.activate
def test_category_attributes_returns_multiple_attributes_as_items(client):
    add(responses.GET, body("Attribute", [{"Id": "name"}, {"Id": "price"}]))

    assert len(client.products.get_category_attributes(1234).items) == 2


@responses.activate
def test_create_exposes_request_id(client):
    raw = {"SuccessResponse": {"Head": {"RequestId": "feed-123"}, "Body": {}}}
    add(responses.POST, raw)

    assert client.products.create("<Request/>").request_id == "feed-123"
