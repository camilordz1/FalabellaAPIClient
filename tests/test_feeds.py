import pytest
import responses

from falabella_sdk import (
    FalabellaAPIError,
    FalabellaFeedError,
    FalabellaFeedTimeout,
    Feeds,
    FeedStatus,
)
from tests.helpers import add, sent_params

FEED = {
    "Feed": "feed-1",
    "Status": "Finished",
    "Action": "ProductUpdate",
    "CreationDate": "2026-11-10 09:12:44",
    "UpdatedDate": "2026-11-10 09:13:02",
    "Source": "api",
    "TotalRecords": "2",
    "ProcessedRecords": "2",
    "FailedRecords": "2",
}


def success(body):
    return {"SuccessResponse": {"Head": {"RequestId": "feed-1"}, "Body": body}}


def detail(**overrides):
    payload = dict(FEED)
    payload.update(overrides)
    return payload


ERROR = {
    "Code": "0",
    "Message": "AnchoDeCorte, FormaUso is/are not applicable to Ferretería",
    "SellerSku": "TP-18545",
}


@responses.activate
def test_list_sends_get_with_feed_list_action(client):
    add(responses.GET, success({"Feed": [FEED]}))

    result = client.feeds.list()

    assert sent_params(responses.calls[0])["Action"] == "FeedList"
    assert responses.calls[0].request.method == "GET"
    assert result.items == [FEED]


@responses.activate
def test_list_returns_single_feed_dict_as_items(client):
    add(responses.GET, success({"Feed": FEED}))

    assert client.feeds.list().items == [FEED]


@responses.activate
def test_list_returns_multiple_feeds_as_items(client):
    add(responses.GET, success({"Feed": [FEED, detail(Feed="feed-2")]}))

    assert len(client.feeds.list().items) == 2


@responses.activate
def test_list_returns_empty_items_for_empty_string(client):
    add(responses.GET, success({"Feed": ""}))

    assert client.feeds.list().items == []


@responses.activate
def test_status_sends_feed_id(client):
    add(responses.GET, success({"FeedDetail": detail()}))

    client.feeds.status("feed-1")

    query = sent_params(responses.calls[0])
    assert responses.calls[0].request.method == "GET"
    assert query["Action"] == "FeedStatus"
    assert query["FeedID"] == "feed-1"


@responses.activate
def test_status_maps_fields_and_converts_counts(client):
    add(
        responses.GET,
        success({"FeedDetail": detail(FeedErrors={"Error": ERROR})}),
    )

    result = client.feeds.status("feed-1")

    assert isinstance(result, FeedStatus)
    assert result.feed_id == "feed-1"
    assert result.status == "Finished"
    assert result.action == "ProductUpdate"
    assert result.creation_date == "2026-11-10 09:12:44"
    assert result.updated_date == "2026-11-10 09:13:02"
    assert result.source == "api"
    assert (result.total_records, result.processed_records, result.failed_records) == (2, 2, 2)
    assert len(result.errors) == 1
    assert result.errors[0].seller_sku == "TP-18545"
    assert result.errors[0].code == "0"
    assert result.errors[0].message == ERROR["Message"]
    assert result.warnings == []


@responses.activate
def test_status_errors_single_dict_is_normalized(client):
    add(responses.GET, success({"FeedDetail": detail(FeedErrors={"Error": ERROR})}))

    assert len(client.feeds.status("feed-1").errors) == 1


@responses.activate
def test_status_errors_list_is_kept(client):
    second = {"Code": "1", "Message": "Other", "SellerSku": "TP-2"}
    add(responses.GET, success({"FeedDetail": detail(FeedErrors={"Error": [ERROR, second]})}))

    assert len(client.feeds.status("feed-1").errors) == 2


@responses.activate
def test_status_without_feed_errors_returns_empty_list(client):
    add(responses.GET, success({"FeedDetail": detail()}))

    assert client.feeds.status("feed-1").errors == []


@responses.activate
def test_status_maps_warnings(client):
    warning = {"Code": "0", "Message": "Deprecated field", "SellerSku": "TP-3"}
    add(responses.GET, success({"FeedDetail": detail(FeedWarnings={"Warning": warning})}))

    result = client.feeds.status("feed-1")

    assert len(result.warnings) == 1
    assert result.warnings[0].seller_sku == "TP-3"


@responses.activate
def test_status_missing_feed_detail_sets_none_fields(client):
    add(responses.GET, success({}))

    result = client.feeds.status("feed-1")

    assert result.feed_id is None
    assert result.status is None
    assert result.action is None
    assert result.creation_date is None
    assert result.updated_date is None
    assert result.source is None
    assert result.total_records is None
    assert result.processed_records is None
    assert result.failed_records is None
    assert result.errors == []
    assert result.warnings == []


@responses.activate
def test_status_invalid_counts_become_none(client):
    add(
        responses.GET,
        success({"FeedDetail": detail(TotalRecords="abc", ProcessedRecords="", FailedRecords=True)}),
    )

    result = client.feeds.status("feed-1")

    assert result.total_records is None
    assert result.processed_records is None
    assert result.failed_records is None


@pytest.mark.parametrize(
    "status, expected",
    [
        ("Finished", True),
        ("Canceled", True),
        ("Error", True),
        ("Queued", False),
        ("Processing", False),
        (None, False),
    ],
)
@responses.activate
def test_is_done(client, status, expected):
    add(responses.GET, success({"FeedDetail": detail(Status=status)}))

    assert client.feeds.status("feed-1").is_done is expected


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"FeedErrors": {"Error": ERROR}, "FailedRecords": "0"}, True),
        ({"FailedRecords": "3"}, True),
        ({"FailedRecords": "0"}, False),
        ({"FailedRecords": None}, False),
    ],
)
@responses.activate
def test_has_errors(client, overrides, expected):
    add(responses.GET, success({"FeedDetail": detail(**overrides)}))

    assert client.feeds.status("feed-1").has_errors is expected


@pytest.mark.parametrize("feed_id", ["", None, 123])
@responses.activate
def test_empty_or_non_string_feed_id_raises_without_request(client, feed_id):
    with pytest.raises(ValueError):
        client.feeds.status(feed_id)

    assert len(responses.calls) == 0


@responses.activate
def test_unknown_feed_raises_api_error(client):
    add(
        responses.GET,
        {
            "ErrorResponse": {
                "Head": {"ErrorCode": "12", "ErrorMessage": "E012: Invalid Feed ID"}
            }
        },
    )

    with pytest.raises(FalabellaAPIError) as exc_info:
        client.feeds.status("missing")

    assert exc_info.value.error_code == "12"


def test_feeds_property_is_lazy_and_cached(client):
    assert isinstance(client.feeds, Feeds)
    assert client.feeds is client.feeds


class FakeTime:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def use_fake_time(client):
    fake = FakeTime()
    client.feeds._clock = fake.clock
    client._sleep = fake.sleep
    return fake


@responses.activate
def test_wait_returns_immediately_when_done(client):
    add(responses.GET, success({"FeedDetail": detail()}))
    fake = use_fake_time(client)

    result = client.feeds.wait("feed-1")

    assert result.is_done
    assert fake.sleeps == []


@responses.activate
def test_wait_polls_until_done_without_extra_sleeps(client):
    for status in ("Queued", "Processing", "Finished"):
        add(responses.GET, success({"FeedDetail": detail(Status=status)}))
    fake = use_fake_time(client)

    result = client.feeds.wait("feed-1")

    assert result.status == "Finished"
    assert fake.sleeps == [5.0, 5.0]


@responses.activate
def test_wait_sleep_is_capped_by_remaining_time(client):
    for _ in range(3):
        add(responses.GET, success({"FeedDetail": detail(Status="Processing")}))
    fake = use_fake_time(client)

    with pytest.raises(FalabellaFeedTimeout) as exc_info:
        client.feeds.wait("feed-1", timeout=7.0, poll_interval=5.0)

    assert fake.sleeps == [5.0, 2.0]
    assert exc_info.value.feed_status.status == "Processing"
    assert str(exc_info.value) == "Feed feed-1 still Processing after 7.0s"


@responses.activate
def test_wait_timeout_keeps_last_status(client):
    add(responses.GET, success({"FeedDetail": detail(Status="Queued")}))
    add(responses.GET, success({"FeedDetail": detail(Status="Queued")}))
    fake = use_fake_time(client)

    with pytest.raises(FalabellaFeedTimeout) as exc_info:
        client.feeds.wait("feed-1", timeout=0.5, poll_interval=1.0)

    assert exc_info.value.feed_status.status == "Queued"
    assert fake.sleeps == [0.5]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"timeout": 0},
        {"timeout": -1},
        {"timeout": True},
        {"poll_interval": 0},
        {"poll_interval": -1},
        {"poll_interval": True},
    ],
)
@responses.activate
def test_wait_invalid_options_raise_without_request(client, kwargs):
    with pytest.raises(ValueError):
        client.feeds.wait("feed-1", **kwargs)

    assert len(responses.calls) == 0


@pytest.mark.parametrize("feed_id", ["", None, 123])
@responses.activate
def test_wait_invalid_feed_id_raises_without_request(client, feed_id):
    with pytest.raises(ValueError):
        client.feeds.wait(feed_id)

    assert len(responses.calls) == 0


@responses.activate
def test_feed_error_message_with_one_error(client):
    add(
        responses.GET,
        success(
            {
                "FeedDetail": detail(
                    FeedErrors={"Error": ERROR}, TotalRecords="1", FailedRecords="1"
                )
            }
        ),
    )
    feed_status = client.feeds.status("feed-1")

    error = FalabellaFeedError(feed_status)

    assert isinstance(error, FalabellaAPIError)
    assert error.action == "ProductUpdate"
    assert error.feed_status is feed_status
    assert error.errors == feed_status.errors
    assert "Feed feed-1 Finished: 1/1 records failed" in str(error)
    assert f"TP-18545: {ERROR['Message']}" in str(error)


@responses.activate
def test_feed_error_message_shows_three_errors_and_the_rest(client):
    errors = [
        {"Code": "0", "Message": f"message-{index}", "SellerSku": f"TP-{index}"}
        for index in range(5)
    ]
    add(
        responses.GET,
        success({"FeedDetail": detail(FeedErrors={"Error": errors}, FailedRecords="5")}),
    )
    feed_status = client.feeds.status("feed-1")

    message = str(FalabellaFeedError(feed_status))

    assert "TP-0: message-0" in message
    assert "TP-1: message-1" in message
    assert "TP-2: message-2" in message
    assert "TP-3: message-3" not in message
    assert message.endswith("(+2 more)")
