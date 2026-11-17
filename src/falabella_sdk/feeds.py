"""Feeds resource for tracking asynchronous write operations."""

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from falabella_sdk.actions import Actions
from falabella_sdk.client import FalabellaFeedError
from falabella_sdk.responses import (
    FalabellaResponse,
    _text,
    _total_count,
    get_list,
    unwrap,
    unwrap_collection,
)

if TYPE_CHECKING:
    from falabella_sdk.client import FalabellaClient

_PENDING_STATUSES = {"Queued", "Processing"}


def _is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _count(element: Dict[str, Any], key: str) -> Optional[int]:
    """Read a count field with the same rules as ``FalabellaResponse.total_count``."""
    return _total_count({"TotalCount": element.get(key)})


def _feed_error(element: Any) -> Optional["FeedError"]:
    if not isinstance(element, dict):
        return None
    return FeedError(
        seller_sku=_text(element, "SellerSku"),
        code=_text(element, "Code"),
        message=_text(element, "Message"),
    )


def _feed_errors(elements: List[Any]) -> List["FeedError"]:
    return [error for error in map(_feed_error, elements) if error is not None]


def _build_status(response: FalabellaResponse) -> "FeedStatus":
    body = response.body if isinstance(response.body, dict) else {}
    detail = body.get("FeedDetail")
    if not isinstance(detail, dict):
        detail = {}
    return FeedStatus(
        feed_id=_text(detail, "Feed"),
        status=_text(detail, "Status"),
        action=_text(detail, "Action"),
        creation_date=_text(detail, "CreationDate"),
        updated_date=_text(detail, "UpdatedDate"),
        source=_text(detail, "Source"),
        total_records=_count(detail, "TotalRecords"),
        processed_records=_count(detail, "ProcessedRecords"),
        failed_records=_count(detail, "FailedRecords"),
        errors=_feed_errors(get_list(detail, "FeedErrors", "Error")),
        warnings=_feed_errors(get_list(detail, "FeedWarnings", "Warning")),
        response=response,
    )


@dataclass(frozen=True)
class FeedError:
    seller_sku: Optional[str]
    code: Optional[str]
    message: Optional[str]


class FalabellaFeedTimeout(FalabellaFeedError):
    """Error raised when waiting for a feed exceeds its timeout."""

    def __init__(self, feed_status: "FeedStatus", timeout: float) -> None:
        super().__init__(
            feed_status,
            message=(
                f"Feed {feed_status.feed_id} still {feed_status.status} after {timeout}s"
            ),
        )


@dataclass(frozen=True)
class FeedStatus:
    feed_id: Optional[str]
    status: Optional[str]
    action: Optional[str]
    creation_date: Optional[str]
    updated_date: Optional[str]
    source: Optional[str]
    total_records: Optional[int]
    processed_records: Optional[int]
    failed_records: Optional[int]
    errors: List[FeedError]
    warnings: List[FeedError]
    response: FalabellaResponse

    @property
    def is_done(self) -> bool:
        """Whether the feed is no longer queued or processing."""
        return bool(self.status) and self.status not in _PENDING_STATUSES

    @property
    def has_errors(self) -> bool:
        """Whether the feed reported errors or failed records."""
        return bool(self.errors) or (self.failed_records or 0) > 0


class Feeds(Actions):
    """Operations for the asynchronous feeds returned by write actions."""

    def __init__(self, client: "FalabellaClient") -> None:
        """Initialize the resource with an authenticated client.

        Args:
            client (FalabellaClient): An initialized Falabella client.
        """
        super().__init__(client)
        self._clock = time.monotonic

    def list(self) -> FalabellaResponse:
        """List recent feeds.

        Returns:
            FalabellaResponse: Feeds in ``items``.
        """
        raw = self.client.query('get', params={"Action": "FeedList"})
        return unwrap_collection(raw, "Feed")

    def status(self, feed_id: str) -> FeedStatus:
        """Get the typed status of one feed.

        Args:
            feed_id: Feed id returned in ``Head.RequestId`` by a write operation.

        Returns:
            FeedStatus: Parsed feed detail, including errors and warnings.

        Raises:
            ValueError: If ``feed_id`` is empty or not a string (no request is sent).
        """
        if not isinstance(feed_id, str) or not feed_id:
            raise ValueError("feed_id must be a non-empty string")
        raw = self.client.query(
            'get', params={"Action": "FeedStatus", "FeedID": feed_id}
        )
        return _build_status(unwrap(raw))

    def wait(self, feed_id: str, *, timeout: float = 300.0,
             poll_interval: float = 5.0) -> FeedStatus:
        """Poll a feed until it is done or the timeout elapses.

        Args:
            feed_id: Feed id returned in ``Head.RequestId`` by a write operation.
            timeout: Maximum seconds to wait.
            poll_interval: Seconds between polls, capped by the remaining time.

        Returns:
            FeedStatus: The last observed status, which is done.

        Raises:
            ValueError: If any argument is invalid (no request is sent).
            FalabellaFeedTimeout: If the feed is still pending when ``timeout`` elapses.
        """
        if not isinstance(feed_id, str) or not feed_id:
            raise ValueError("feed_id must be a non-empty string")
        if not _is_positive_number(timeout):
            raise ValueError("timeout must be a positive number")
        if not _is_positive_number(poll_interval):
            raise ValueError("poll_interval must be a positive number")

        started = self._clock()
        while True:
            feed_status = self.status(feed_id)
            if feed_status.is_done:
                return feed_status
            remaining = timeout - (self._clock() - started)
            if remaining <= 0:
                raise FalabellaFeedTimeout(feed_status, timeout)
            self.client._sleep(min(poll_interval, remaining))
