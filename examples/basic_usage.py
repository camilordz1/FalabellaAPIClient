"""Minimal example for the Falabella Seller Center API client.

Required environment variables:
    FALABELLA_USER       Seller account email (UserID).
    FALABELLA_API_KEY    API key.
    FALABELLA_SELLER_ID  Seller id used in the required User-Agent header.

Optional environment variables:
    FALABELLA_BUSINESS_UNIT  FACL (Chile), FACO (Colombia) or FAPE (Peru). Default: FACO.
    FALABELLA_SKU            Product SKU to fetch. Default: TP-19150.
    FALABELLA_ORDER_ID       Order id to fetch. Default: 100513.

The example only reads data. Write operations return a feed id; to wait for the feed and get
per-SKU errors, use for example:

    status = client.products.update(xml, wait=True, timeout=120)  # raises FalabellaFeedError
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
        products = client.products.get(SkuSellerList=json.dumps([sku]))
        for product in products.items:
            print("product:", product.get("SellerSku"), "-", product.get("Name"))

        for feed in client.feeds.list().items[:5]:
            status = client.feeds.status(feed["Feed"])
            print("feed:", status.action, status.status, f"failed={status.failed_records}")
            for error in status.errors:
                print("   ", error.seller_sku, "-", error.message)

        orders = client.orders.get(order_id)
        print("orders found:", len(orders.items))

        items = client.orders.items(order_id)
        print("order items:", len(items.items))
    except FalabellaAPIError as exc:
        print(
            f"Falabella API error: {exc} (status: {exc.status_code})",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
