"""Feeds resource for tracking asynchronous write operations."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from falabella_sdk.actions import Actions
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

_DONE_STATUSES = {"Finished", "Canceled"}


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
        """Whether the feed reached a final state."""
        return self.status in _DONE_STATUSES

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
