from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree

import pytest

from falabella_sdk import images_to_xml, to_xml

GOLDEN = Path(__file__).parent / "golden"

PRICE_STOCK_UPDATE = {
    "SellerSku": "TP-10490",
    "BusinessUnits": {
        "BusinessUnit": {
            "OperatorCode": "faco",
            "Price": Decimal("310000.00"),
            "Stock": 5,
        }
    },
}

TWO_PRODUCTS = [
    {"SellerSku": "TP-1", "Name": "Uno"},
    {"SellerSku": "TP-2", "Name": "Dos"},
]

CREATE_FULL = {
    "SellerSku": "TP-10490",
    "Name": "Taladro",
    "Brand": "TRUPER",
    "PrimaryCategory": "3177",
    "Variation": "...",
    "Description": "<p><strong>Ferretería</strong> ñ</p>",
    "ProductData": {"ConditionType": "Nuevo", "Model": "10490"},
}

REMOVE = {"SellerSku": "TP-1"}


@pytest.mark.parametrize(
    "payload, filename",
    [
        (PRICE_STOCK_UPDATE, "price_stock_update.xml"),
        (TWO_PRODUCTS, "two_products.xml"),
        (CREATE_FULL, "create_full.xml"),
        (REMOVE, "remove.xml"),
    ],
)
def test_to_xml_matches_golden(payload, filename):
    assert to_xml(payload) == (GOLDEN / filename).read_bytes()


def test_text_is_escaped_and_round_trips():
    xml = to_xml({"SellerSku": "A", "Name": "A & B <x>"})

    assert b"A &amp; B &lt;x&gt;" in xml
    assert ElementTree.fromstring(xml).findtext("./Product/Name") == "A & B <x>"


def test_description_is_emitted_as_cdata():
    html = "<p><strong>Ferretería</strong> ñ</p>"

    xml = to_xml({"SellerSku": "A", "Description": html})

    assert b"<![CDATA[" in xml
    assert ElementTree.fromstring(xml).findtext("./Product/Description") == html


def test_description_with_cdata_terminator_round_trips():
    html = "before ]]> after"

    xml = to_xml({"SellerSku": "A", "Description": html})

    assert ElementTree.fromstring(xml).findtext("./Product/Description") == html


def test_none_omits_and_empty_string_keeps_empty_element():
    xml = to_xml({"SellerSku": "A", "Name": None, "Brand": ""})

    assert b"<Name>" not in xml
    assert b"<Brand></Brand>" in xml


def test_list_repeats_element():
    xml = to_xml({"SellerSku": "A", "Image": ["a", "b"]})

    assert b"<Image>a</Image><Image>b</Image>" in xml


def test_keys_preserve_insertion_order():
    xml = to_xml({"SellerSku": "A", "Name": "N", "Brand": "B"})

    assert xml.index(b"<Name>") < xml.index(b"<Brand>")


def test_numbers_are_stringified():
    xml = to_xml(
        {
            "SellerSku": "A",
            "Stock": 5,
            "Weight": 1.5,
            "Price": Decimal("310000.00"),
        }
    )

    assert b"<Stock>5</Stock>" in xml
    assert b"<Weight>1.5</Weight>" in xml
    assert b"<Price>310000.00</Price>" in xml


def test_bool_value_is_rejected():
    with pytest.raises(TypeError):
        to_xml({"SellerSku": "A", "Name": True})


def test_invalid_key_is_rejected():
    with pytest.raises(ValueError):
        to_xml({"SellerSku": "A", "Bad Key": "x"})


@pytest.mark.parametrize("product", [{"Name": "x"}, {"SellerSku": ""}])
def test_missing_or_empty_seller_sku_is_rejected(product):
    with pytest.raises(ValueError):
        to_xml(product)


def test_empty_product_list_is_rejected():
    with pytest.raises(ValueError):
        to_xml([])


def test_object_value_is_rejected():
    with pytest.raises(TypeError):
        to_xml({"SellerSku": "A", "Name": object()})


def test_non_dict_product_in_list_is_rejected():
    with pytest.raises(TypeError):
        to_xml([{"SellerSku": "A"}, "x"])


@pytest.mark.parametrize("text", ["bad\x00", "tab\x0bvertical", "form\x0cfeed", "esc\x1b"])
@pytest.mark.parametrize("key", ["Name", "Description"])
def test_text_with_xml_invalid_characters_is_rejected(key, text):
    """A control character makes the whole feed invalid XML, so fail before sending."""
    with pytest.raises(ValueError, match=key):
        to_xml({"SellerSku": "TP-1", key: text})


def test_tab_newline_and_carriage_return_are_allowed():
    xml = to_xml({"SellerSku": "TP-1", "Name": "a\tb\nc\rd"})

    assert ElementTree.fromstring(xml).find(".//Name") is not None


@pytest.mark.parametrize("sku", ["  ", "\t\n"])
def test_blank_seller_sku_is_rejected(sku):
    with pytest.raises(ValueError, match="SellerSku"):
        to_xml({"SellerSku": sku})


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), float("-inf"), Decimal("NaN"), Decimal("Infinity")]
)
def test_non_finite_numbers_are_rejected(value):
    with pytest.raises(ValueError, match="Price"):
        to_xml({"SellerSku": "TP-1", "BusinessUnits": {"BusinessUnit": {"Price": value}}})


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (Decimal("1E+3"), "1000"),
        (Decimal("49800.00"), "49800.00"),
        (Decimal("1E+10"), "10000000000"),
        (1.5, "1.5"),
    ],
)
def test_numbers_are_written_without_exponent(value, text):
    xml = to_xml({"SellerSku": "TP-1", "BusinessUnits": {"BusinessUnit": {"Price": value}}})

    assert ElementTree.fromstring(xml).find(".//Price").text == text


def test_only_the_product_description_uses_cdata():
    xml = to_xml(
        {"SellerSku": "TP-1", "Description": "<p>x</p>", "ProductData": {"Description": "<b>"}}
    ).decode()

    assert "<Description><![CDATA[<p>x</p>]]></Description>" in xml
    assert "<ProductData><Description>&lt;b&gt;</Description></ProductData>" in xml


@pytest.mark.parametrize("value", [10**15, Decimal("1E+16"), -1e15])
def test_number_at_or_above_limit_is_rejected(value):
    with pytest.raises(ValueError):
        to_xml({"SellerSku": "A", "Stock": value})


def test_number_below_limit_is_allowed():
    xml = to_xml({"SellerSku": "A", "Stock": 999999999999999})

    assert b"<Stock>999999999999999</Stock>" in xml


@pytest.mark.parametrize("value", [10**18, Decimal("123456789012345678")])
def test_large_numbers_are_allowed_outside_price_and_stock(value):
    xml = to_xml({"SellerSku": "TP-1", "ProductData": {"Ean": value}})

    assert ElementTree.fromstring(xml).find(".//Ean").text == str(value)


def test_absurd_exponent_is_rejected_anywhere():
    """Fixed-point output must not expand Decimal('1E+1000000') to a million digits."""
    with pytest.raises(ValueError, match="Ean"):
        to_xml({"SellerSku": "TP-1", "ProductData": {"Ean": Decimal("1E+1000000")}})


IMAGES = {
    "TP-10490": ["https://cdn.example.com/1.jpg", "https://cdn.example.com/2.jpg"],
    "TP-13027": ["https://cdn.example.com/a.jpg?w=100&h=200"],
}


def test_images_to_xml_matches_golden():
    assert images_to_xml(IMAGES) == (GOLDEN / "images.xml").read_bytes()


def test_images_to_xml_escapes_and_round_trips_urls():
    xml = images_to_xml(IMAGES)

    root = ElementTree.fromstring(xml)
    urls = [image.text for image in root.findall(".//ProductImage/Images/Image")]
    assert urls == [
        "https://cdn.example.com/1.jpg",
        "https://cdn.example.com/2.jpg",
        "https://cdn.example.com/a.jpg?w=100&h=200",
    ]


@pytest.mark.parametrize(
    "images",
    [
        {},
        {" ": ["https://a/1.jpg"]},
        {"TP-1": []},
        {"TP-1": [f"https://a/{index}.jpg" for index in range(9)]},
        {"TP-1": [123]},
        {"TP-1": ["http://a/1.jpg"]},
        {"TP-1": ["https://a/1.jpg", "https://a/1.jpg"]},
        {"TP-1": ["https://a/1.jpg\x01"]},
    ],
)
def test_images_to_xml_rejects_invalid_input(images):
    with pytest.raises(ValueError):
        images_to_xml(images)
