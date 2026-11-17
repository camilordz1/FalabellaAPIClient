"""Helpers to unwrap Falabella Seller Center response envelopes."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(head: Dict[str, Any], key: str) -> Optional[str]:
    value = head.get(key)
    return value if isinstance(value, str) and value else None


def _total_count(head: Dict[str, Any]) -> Optional[int]:
    value = head.get("TotalCount")
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


@dataclass(frozen=True)
class FalabellaResponse:
    """Unwrapped view of a Falabella API response envelope."""

    head: Dict[str, Any]
    body: Any
    raw: Any

    @property
    def request_id(self) -> Optional[str]:
        """Value of ``Head.RequestId``; ``None`` when missing or empty."""
        return _text(self.head, "RequestId")

    @property
    def request_action(self) -> Optional[str]:
        """Value of ``Head.RequestAction``; ``None`` when missing or empty."""
        return _text(self.head, "RequestAction")

    @property
    def response_type(self) -> Optional[str]:
        """Value of ``Head.ResponseType``; ``None`` when missing or empty."""
        return _text(self.head, "ResponseType")

    @property
    def total_count(self) -> Optional[int]:
        """``Head.TotalCount`` as an int; ``None`` when missing or invalid."""
        return _total_count(self.head)


def unwrap(raw: Any) -> FalabellaResponse:
    """Unwrap a ``SuccessResponse`` envelope without normalizing its body.

    Args:
        raw: Parsed JSON returned by ``FalabellaClient.query``.

    Returns:
        FalabellaResponse: Extracted ``head``/``body`` plus the untouched ``raw`` input.

    Raises:
        ValueError: If ``raw`` is an ``ErrorResponse``. Those are raised as
            ``FalabellaAPIError`` by ``FalabellaClient.query``, so reaching this
            function with one indicates a programming error.

    Non-envelope values (``{}``, ``{"response_text": ...}``, lists, ``None``) are
    returned unchanged as ``body`` with an empty ``head``.
    """
    if isinstance(raw, dict):
        if "ErrorResponse" in raw:
            raise ValueError("ErrorResponse envelopes must be handled by FalabellaClient.query")
        success = raw.get("SuccessResponse")
        if isinstance(success, dict):
            return FalabellaResponse(
                head=_as_dict(success.get("Head")),
                body=_as_dict(success.get("Body")),
                raw=raw,
            )
    return FalabellaResponse(head={}, body=raw, raw=raw)
