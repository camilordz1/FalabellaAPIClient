"""Typed payloads for product writes and their XML serializer."""

import re
from decimal import Decimal
from typing import Any, Dict, List, TypedDict, Union
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


def _validate_name(name: str) -> None:
    if not isinstance(name, str) or not _XML_NAME.match(name):
        raise ValueError(f"Invalid XML element name: {name!r}")


def _scalar_text(value: Any, key: str) -> str:
    if isinstance(value, bool):
        raise TypeError(f"Unsupported bool value for key {key!r}")
    if isinstance(value, (str, int, float, Decimal)):
        return str(value)
    raise TypeError(f"Unsupported value type for key {key!r}: {type(value).__name__}")


def _element(name: str, value: Any) -> str:
    _validate_name(name)
    if value is None:
        return ""
    if isinstance(value, list):
        return "".join(_element(name, item) for item in value)
    if isinstance(value, dict):
        children = "".join(
            _element(child_name, child_value) for child_name, child_value in value.items()
        )
        return f"<{name}>{children}</{name}>"

    text = _scalar_text(value, name)
    if name == "Description":
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
        if not isinstance(seller_sku, str) or not seller_sku:
            raise ValueError("each product requires a non-empty SellerSku")

    body = "".join(_element("Product", product) for product in items)
    return f"{_HEADER}<Request>{body}</Request>".encode("utf-8")
