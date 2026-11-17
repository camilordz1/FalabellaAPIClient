"""Minimal example for the Falabella Seller Center API client.

Required environment variables:
    FALABELLA_USER       Seller account email (UserID).
    FALABELLA_API_KEY    API key.
    FALABELLA_SELLER_ID  Seller id used in the required User-Agent header.

Optional environment variables:
    FALABELLA_BUSINESS_UNIT  FACL (Chile), FACO (Colombia) or FAPE (Peru). Default: FACO.
    FALABELLA_SKU            Product SKU to fetch. Default: TP-19150.
    FALABELLA_ORDER_ID       Order id to fetch. Default: 100513.
"""
import json
import os
import sys

from falabella_sdk import FalabellaAPIError, FalabellaClient

REQUIRED_VARIABLES = ("FALABELLA_USER", "FALABELLA_API_KEY", "FALABELLA_SELLER_ID")


def main() -> int:
    missing = [name for name in REQUIRED_VARIABLES if not os.environ.get(name)]
    if missing:
        print(
            f"Missing required environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1

    client = FalabellaClient(
        user=os.environ["FALABELLA_USER"],
        key=os.environ["FALABELLA_API_KEY"],
        seller_id=os.environ["FALABELLA_SELLER_ID"],
        business_unit=os.environ.get("FALABELLA_BUSINESS_UNIT", "FACO"),
    )

    sku = os.environ.get("FALABELLA_SKU", "TP-19150")
    order_id = os.environ.get("FALABELLA_ORDER_ID", "100513")

    try:
        product = client.products.get(SkuSellerList=json.dumps([sku]))
        print("product:", product)

        order = client.orders.get(order_id)
        print("order:", order)

        items = client.orders.items(order_id)
        print("orderItems:", items)
    except FalabellaAPIError as exc:
        print(
            f"Falabella API error: {exc} (status: {exc.status_code})",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
