"""Typed payloads for product writes and their XML serializer."""

import re
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Dict, List, TypedDict, Union
from urllib.parse import urlsplit
from xml.sax.saxutils import escape


class BusinessUnit(TypedDict, total=False):
    OperatorCode: Union[str, int, float, Decimal]
    Price: Union[str, int, float, Decimal]
    SpecialPrice: Union[str, int, float, Decimal]
    SpecialFromDate: Union[str, int, float, Decimal]
    SpecialToDate: Union[str, int, float, Decimal]
    Stock: Union[str, int, float, Decimal]
    Status: Union[str, int, float, Decimal]


class BusinessUnits(TypedDict, total=False):
    BusinessUnit: Union[BusinessUnit, List[BusinessUnit]]


class _ProductRequired(TypedDict):
    SellerSku: str


class _PriceStockUpdateRequired(TypedDict):
    SellerSku: str


class PriceStockUpdate(_PriceStockUpdateRequired, total=False):
    Price: Union[str, int, float, Decimal]
    Stock: Union[str, int, float, Decimal]
    SpecialPrice: Union[str, int, float, Decimal]
    SpecialFromDate: Union[str, int, float, Decimal]
    SpecialToDate: Union[str, int, float, Decimal]
    Status: Union[str, int, float, Decimal]


class Product(_ProductRequired, total=False):
    ParentSku: str
    Name: str
    Description: str
    Brand: str
    PrimaryCategory: str
    Categories: str
    Variation: str
    Color: str
    ColorBasico: str
    Size: str
    BusinessUnits: BusinessUnits
    ProductData: Dict[str, Any]


_HEADER = '<?xml version="1.0" encoding="UTF-8" ?>\n'
_XML_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
# XML 1.0 forbids C0 controls except tab, newline and carriage return, and U+FFFE/U+FFFF.
_XML_INVALID_CHARS = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")
# Prices and stock are far below this; it catches typos such as an extra exponent.
_MAX_ABS_NUMBER = 10**15
_BOUNDED_KEYS = frozenset({"Price", "SpecialPrice", "Stock"})
# Fixed-point output of larger exponents would expand to an absurd number of digits.
_MAX_DECIMAL_EXPONENT = 30


def _validate_name(name: str) -> None:
    if not isinstance(name, str) or not _XML_NAME.match(name):
        raise ValueError(f"Invalid XML element name: {name!r}")


def _scalar_text(value: Any, key: str) -> str:
    if isinstance(value, bool):
        raise TypeError(f"Unsupported bool value for key {key!r}")
    if isinstance(value, (float, Decimal)):
        number = Decimal(repr(value)) if isinstance(value, float) else value
        if not number.is_finite():
            raise ValueError(f"Value for key {key!r} must be a finite number")
        if number and number.adjusted() > _MAX_DECIMAL_EXPONENT:
            raise ValueError(f"Value for key {key!r} is too large")
        if key in _BOUNDED_KEYS and abs(number) >= _MAX_ABS_NUMBER:
            raise ValueError(f"Value for key {key!r} must be below 10**15")
        # Fixed-point text: Decimal("1E+3") -> "1000", 1e20 -> "100000000000000000000".
        return format(number, "f")
    if isinstance(value, int):
        if key in _BOUNDED_KEYS and abs(value) >= _MAX_ABS_NUMBER:
            raise ValueError(f"Value for key {key!r} must be below 10**15")
        text = str(value)
        if _XML_INVALID_CHARS.search(text):
            raise ValueError(f"Value for key {key!r} has characters not allowed in XML")
        return text
    if isinstance(value, str):
        text = value
        if _XML_INVALID_CHARS.search(text):
            raise ValueError(f"Value for key {key!r} has characters not allowed in XML")
        return text
    raise TypeError(f"Unsupported value type for key {key!r}: {type(value).__name__}")


def _element(name: str, value: Any, parent: str = "") -> str:
    _validate_name(name)
    if value is None:
        return ""
    if isinstance(value, list):
        return "".join(_element(name, item, parent) for item in value)
    if isinstance(value, dict):
        children = "".join(
            _element(child_name, child_value, name) for child_name, child_value in value.items()
        )
        return f"<{name}>{children}</{name}>"

    text = _scalar_text(value, name)
    # Only the product description carries HTML; any other "Description" is plain text.
    if name == "Description" and parent == "Product":
        text = text.replace("]]>", "]]]]><![CDATA[>")
        return f"<{name}><![CDATA[{text}]]></{name}>"
    return f"<{name}>{escape(text)}</{name}>"


def to_xml(products: Union[Product, List[Product]]) -> bytes:
    """Serialize one product or a list of products to Falabella write XML.

    Args:
        products: Product dict(s) using the API key names.

    Returns:
        bytes: UTF-8 XML starting with the declared header and a ``<Request>`` root.

    Raises:
        TypeError: If a product is not a dict, a product list has non-dict items,
            a value is a bool or has another unsupported type.
        ValueError: If the list is empty, a product lacks a non-empty ``SellerSku``,
            or a key is not a valid XML name.
    """
    if isinstance(products, dict):
        items = [products]
    elif isinstance(products, (list, tuple)):
        items = list(products)
    else:
        raise TypeError("products must be a dict or a list of dicts")

    if not items:
        raise ValueError("products must not be empty")

    for product in items:
        if not isinstance(product, dict):
            raise TypeError("each product must be a dict")
        seller_sku = product.get("SellerSku")
        if not isinstance(seller_sku, str) or not seller_sku.strip():
            raise ValueError("each product requires a non-empty SellerSku")

    body = "".join(_element("Product", product) for product in items)
    return f"{_HEADER}<Request>{body}</Request>".encode("utf-8")


def images_to_xml(images: Mapping[str, Sequence[str]]) -> bytes:
    """Serialize per-SKU image URLs to the ``Image`` action XML.

    Args:
        images: Mapping of ``SellerSku`` to 1–8 public ``https://`` URLs.

    Returns:
        bytes: UTF-8 XML with one ``<ProductImage>`` per SKU.

    Raises:
        ValueError: If the mapping is empty, a SKU is blank, a SKU has 0 or more
            than 8 URLs, a URL is not a ``https://`` string, a URL is duplicated
            for the same SKU, or text contains characters not allowed in XML.
    """
    if not isinstance(images, Mapping) or not images:
        raise ValueError("images must be a non-empty mapping of SellerSku to URLs")

    validated = []
    for seller_sku, urls in images.items():
        if not isinstance(seller_sku, str) or not seller_sku.strip():
            raise ValueError("each SellerSku must be a non-empty string")
        if _XML_INVALID_CHARS.search(seller_sku):
            raise ValueError(f"SellerSku {seller_sku!r} has characters not allowed in XML")
        if not isinstance(urls, (list, tuple)) or not 1 <= len(urls) <= 8:
            raise ValueError(f"{seller_sku} must have between 1 and 8 image URLs")

        seen = set()
        for url in urls:
            if not isinstance(url, str) or not url.startswith("https://"):
                raise ValueError(f"image URL for {seller_sku} must be a https:// string")
            if not urlsplit(url).netloc or any(char.isspace() for char in url):
                raise ValueError(
                    f"image URL for {seller_sku} needs a host and no spaces: {url!r}"
                )
            if _XML_INVALID_CHARS.search(url):
                raise ValueError(f"image URL for {seller_sku} has characters not allowed in XML")
            if url in seen:
                raise ValueError(f"duplicate image URL for {seller_sku}: {url}")
            seen.add(url)
        validated.append((seller_sku, list(urls)))

    body = "".join(
        _element("ProductImage", {"SellerSku": seller_sku, "Images": {"Image": urls}})
        for seller_sku, urls in validated
    )
    return f"{_HEADER}<Request>{body}</Request>".encode("utf-8")
