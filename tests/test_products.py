import re

import pytest
import requests
import responses

from falabella_sdk import (
    FalabellaAPIError,
    FalabellaFeedError,
    FalabellaFeedTimeout,
    FalabellaResponse,
    FeedStatus,
)
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
def test_brands_accepts_documented_shape_with_several_brands(client):
    """Docs shape: Body.Brands.Brand is a list (live API sends a list of wrappers)."""
    add(responses.GET, body("Brands", {"Brand": [{"Id": 1}, {"Id": 2}]}))

    assert client.products.brands().items == [{"Id": 1}, {"Id": 2}]


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


FEED_FINISHED = {
    "Feed": "feed-1",
    "Status": "Finished",
    "Action": "ProductUpdate",
    "TotalRecords": "1",
    "ProcessedRecords": "1",
    "FailedRecords": "0",
}
FEED_ERROR = {"Code": "0", "Message": "Not applicable", "SellerSku": "TP-18545"}


def write_response(feed_id="feed-1"):
    return {"SuccessResponse": {"Head": {"RequestId": feed_id}, "Body": {}}}


def feed_response(**overrides):
    payload = dict(FEED_FINISHED)
    payload.update(overrides)
    return {"SuccessResponse": {"Head": {}, "Body": {"FeedDetail": payload}}}


@responses.activate
def test_update_wait_returns_feed_status(client):
    add(responses.POST, write_response())
    add(responses.GET, feed_response())

    result = client.products.update("<Request/>", wait=True)

    assert isinstance(result, FeedStatus)
    assert result.processed_records == 1
    assert len(responses.calls) == 2


@responses.activate
def test_update_wait_raises_feed_error_with_sku(client):
    add(responses.POST, write_response())
    add(
        responses.GET,
        feed_response(FailedRecords="1", FeedErrors={"Error": FEED_ERROR}),
    )

    with pytest.raises(FalabellaFeedError) as exc_info:
        client.products.update("<Request/>", wait=True)

    assert exc_info.value.errors[0].seller_sku == "TP-18545"


@responses.activate
def test_update_wait_raises_for_canceled_feed(client):
    add(responses.POST, write_response())
    add(responses.GET, feed_response(Status="Canceled"))

    with pytest.raises(FalabellaFeedError):
        client.products.update("<Request/>", wait=True)


@responses.activate
def test_update_wait_without_feed_id_raises(client):
    add(responses.POST, write_response(feed_id=""))

    with pytest.raises(FalabellaAPIError) as exc_info:
        client.products.update("<Request/>", wait=True)

    assert "no feed id" in str(exc_info.value)
    assert len(responses.calls) == 1


@responses.activate
def test_update_wait_false_returns_response_with_one_request(client):
    add(responses.POST, write_response())

    result = client.products.update("<Request/>")

    assert isinstance(result, FalabellaResponse)
    assert len(responses.calls) == 1


@pytest.mark.parametrize("method", ["create", "update", "remove"])
@pytest.mark.parametrize(
    "options", [{"timeout": 0}, {"timeout": True}, {"poll_interval": -1}]
)
@responses.activate
def test_wait_options_are_validated_before_sending_the_write(client, method, options):
    """An invalid wait option must not send the write: a retry would duplicate the feed."""
    add(responses.POST)

    with pytest.raises(ValueError):
        getattr(client.products, method)("<Request/>", wait=True, **options)

    assert len(responses.calls) == 0


@responses.activate
def test_update_wait_polling_failure_keeps_feed_id(client):
    """The write was already sent: the error must say which feed to check later."""
    add(responses.POST, write_response("feed-42"))
    responses.add(
        responses.GET, re.compile(r"https://sellercenter-api"), body=requests.ConnectionError("down")
    )
    client.max_retries = 0

    with pytest.raises(FalabellaAPIError) as exc_info:
        client.products.update("<Request/>", wait=True)

    assert not isinstance(exc_info.value, FalabellaFeedError)
    assert exc_info.value.feed_id == "feed-42"


@responses.activate
def test_update_wait_feed_error_exposes_feed_id(client):
    add(responses.POST, write_response("feed-7"))
    add(responses.GET, feed_response(Feed="feed-7", Status="Canceled"))

    with pytest.raises(FalabellaFeedError) as exc_info:
        client.products.update("<Request/>", wait=True)

    assert exc_info.value.feed_id == "feed-7"


@responses.activate
def test_update_wait_timeout_raises_with_feed_id(client):
    add(responses.POST, write_response("feed-9"))
    add(responses.GET, feed_response(Feed="feed-9", Status="Processing"))
    now = [0.0]
    client._sleep = lambda seconds: now.__setitem__(0, now[0] + seconds)
    client.feeds._clock = lambda: now[0]

    with pytest.raises(FalabellaFeedTimeout) as exc_info:
        client.products.update("<Request/>", wait=True, timeout=10, poll_interval=5)

    assert exc_info.value.feed_id == "feed-9"
    assert exc_info.value.feed_status.status == "Processing"


@responses.activate
def test_update_wait_feed_error_falls_back_to_write_feed_id(client):
    """FeedDetail without Feed: the error still carries the id returned by the write."""
    add(responses.POST, write_response("feed-5"))
    add(responses.GET, feed_response(Feed=None, Status="Canceled"))

    with pytest.raises(FalabellaFeedError) as exc_info:
        client.products.update("<Request/>", wait=True)

    assert exc_info.value.feed_id == "feed-5"
