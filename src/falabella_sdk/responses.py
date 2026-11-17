"""Helpers to unwrap Falabella Seller Center response envelopes."""

from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional


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
    items: List[Any] = field(default_factory=list)

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
        A ``Body`` of ``None``, ``""`` or missing becomes ``{}``; any other value
        (dict, list, string) is kept as is.

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
            body = success.get("Body")
            if body is None or body == "":
                body = {}
            return FalabellaResponse(
                head=_as_dict(success.get("Head")),
                body=body,
                raw=raw,
            )
    return FalabellaResponse(head={}, body=raw, raw=raw)


def as_list(value: Any) -> list:
    """Return ``value`` as a list without copying dicts or lists.

    ``None`` and ``""`` mean "no items" and return ``[]``. A dict is wrapped in a
    single-element list; a list is returned as is; any other value is wrapped.
    """
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def get_list(container: Any, *path: str) -> list:
    """Read a collection at ``path`` and return it as a list.

    Args:
        container: Parsed response body (usually ``FalabellaResponse.body``).
        *path: Keys to walk through nested dicts. At least one is required.

    Returns:
        list: ``as_list`` of the value at ``path``, or ``[]`` when a step is missing
        or an intermediate value is not a dict.

    Raises:
        TypeError: If no path is provided.
    """
    if not path:
        raise TypeError("get_list requires at least one key")
    current = container
    for key in path:
        if not isinstance(current, dict):
            return []
        current = current.get(key)
    return as_list(current)


def unwrap_collection(raw: Any, *path: str,
                      item_key: Optional[str] = None) -> FalabellaResponse:
    """Unwrap a response whose body contains a collection.

    Args:
        raw: Parsed JSON returned by ``FalabellaClient.query``.
        *path: Keys that lead to the collection inside the unwrapped body.
        item_key: When given, elements that are dicts containing this key are
            replaced by ``element[item_key]``; other elements are left unchanged.
            An unwrapped list is flattened into ``items``, so both
            ``[{"Brand": {...}}, ...]`` and ``{"Brand": [...]}`` give the inner dicts.

    Returns:
        FalabellaResponse: ``unwrap(raw)`` with ``items`` filled from ``get_list``.
    """
    response = unwrap(raw)
    items = get_list(response.body, *path)
    if item_key is not None:
        unwrapped: List[Any] = []
        for element in items:
            if isinstance(element, dict) and item_key in element:
                unwrapped.extend(as_list(element[item_key]))
            else:
                unwrapped.append(element)
        items = unwrapped
    return replace(response, items=items)
