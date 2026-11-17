import importlib

import falabella_sdk


def test_version():
    assert falabella_sdk.__version__ == "1.0.0a1"


def test_public_api():
    expected = {
        "FalabellaClient",
        "FalabellaAPIError",
        "FalabellaResponse",
        "Products",
        "Orders",
        "Seller",
        "Shipments",
        "__version__",
    }
    assert set(falabella_sdk.__all__) == expected
    for name in expected:
        assert hasattr(falabella_sdk, name)


def test_old_import_name_is_gone():
    try:
        importlib.import_module("FalabellaAPIClient")
    except ModuleNotFoundError:
        return
    raise AssertionError("FalabellaAPIClient should not be importable")
