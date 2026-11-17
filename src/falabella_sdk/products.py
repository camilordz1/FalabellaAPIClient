import json
from typing import TYPE_CHECKING, Any, Sequence, Union

from falabella_sdk.actions import Actions
from falabella_sdk.client import FalabellaAPIError, FalabellaFeedError
from falabella_sdk.feeds import validate_wait_options
from falabella_sdk.payloads import PriceStockUpdate, Product, to_xml
from falabella_sdk.responses import FalabellaResponse, unwrap, unwrap_collection

if TYPE_CHECKING:
    from falabella_sdk.client import FalabellaClient
    from falabella_sdk.feeds import FeedStatus

ProductPayload = Union[str, bytes, Product, Sequence[Product]]

_PRICE_STOCK_FIELDS = (
    "Price",
    "Stock",
    "SpecialPrice",
    "SpecialFromDate",
    "SpecialToDate",
    "Status",
)


def _xml_payload(payload: ProductPayload) -> Any:
    if isinstance(payload, (dict, list, tuple)):
        return to_xml(payload)
    if isinstance(payload, (str, bytes)):
        return payload
    raise TypeError("payload must be XML (str or bytes), a product dict or a list of them")


def _find_business_unit(product: Any, operator_code: str) -> dict:
    business_units = product.get("BusinessUnits") if isinstance(product, dict) else None
    if not isinstance(business_units, dict):
        return {}
    units = business_units.get("BusinessUnit")
    if isinstance(units, dict):
        units = [units]
    if not isinstance(units, list):
        return {}
    for unit in units:
        if (isinstance(unit, dict)
                and str(unit.get("OperatorCode", "")).lower() == operator_code):
            return unit
    return {}


class Products(Actions):
    """Operaciones relacionadas con el recurso de Productos en la API de Falabella."""

    def __init__(self, client: "FalabellaClient") -> None:
        """Initialize the resource with an authenticated client.

        Args:
            client (FalabellaClient): An initialized Falabella client.
        """
        super().__init__(client)

    def _wait_for_feed(self, response: FalabellaResponse, action: str,
                       timeout: float, poll_interval: float) -> "FeedStatus":
        if response.request_id is None:
            raise FalabellaAPIError(
                "Write response has no feed id to wait for", action=action
            )
        try:
            feed_status = self.client.feeds.wait(
                response.request_id, timeout=timeout, poll_interval=poll_interval
            )
        except FalabellaAPIError as error:
            # The write is already sent: keep its feed id so the caller can check it later.
            if error.feed_id is None:
                error.feed_id = response.request_id
            raise
        if feed_status.has_errors or feed_status.status != "Finished":
            raise FalabellaFeedError(feed_status, feed_id=response.request_id)
        return feed_status

    def get(self, limit: int = 1000, **kwargs: Any) -> FalabellaResponse:
        """Obtiene información de uno o varios productos.

        Args:
            limit (int, optional): Número máximo de resultados (1 a 1000). Por defecto es 1000.
            **kwargs: Filtros adicionales (e.g., SkuSellerList, Search, CreatedAfter, etc.).

        Returns:
            FalabellaResponse: Response with products in ``items``.
        """
        params = {
            "Action": "GetProducts",
            "Limit": limit
        }

        if kwargs:
            params.update(kwargs)

        return unwrap_collection(
            self.client.query('get', params=params), "Products", "Product"
        )

    def create(self, payload: ProductPayload, *, wait: bool = False, timeout: float = 300.0,
               poll_interval: float = 5.0) -> Union[FalabellaResponse, "FeedStatus"]:
        """Crea nuevos productos en la plataforma.

        Args:
            payload (dict | list[dict] | str | bytes): Producto(s) con los nombres de la API,
                por ejemplo ``{"SellerSku": "TP-1", "Name": "Taladro"}``, o XML.
            wait (bool, optional): Esperar a que el feed termine. Por defecto es False.
            timeout (float, optional): Segundos máximos de espera. Por defecto es 300.0.
            poll_interval (float, optional): Segundos entre consultas. Por defecto es 5.0.

        Returns:
            FalabellaResponse: Response whose ``request_id`` is the feed id when
                ``wait=False``.
            FeedStatus: The finished feed when ``wait=True``.
        """
        params = {
            "Action": "ProductCreate"
        }

        if wait:
            # Validate before sending: a write that fails afterwards would be retried.
            validate_wait_options(timeout, poll_interval)
        payload = _xml_payload(payload)
        response = unwrap(self.client.query('post', params=params, payload=payload))
        if wait:
            return self._wait_for_feed(response, "ProductCreate", timeout, poll_interval)
        return response

    def update(self, payload: ProductPayload, *, wait: bool = False, timeout: float = 300.0,
               poll_interval: float = 5.0) -> Union[FalabellaResponse, "FeedStatus"]:
        """Actualiza productos existentes.

        Args:
            payload (dict | list[dict] | str | bytes): Producto(s) con los nombres de la API,
                por ejemplo ``{"SellerSku": "TP-1", "Stock": 5}``, o XML.
            wait (bool, optional): Esperar a que el feed termine. Por defecto es False.
            timeout (float, optional): Segundos máximos de espera. Por defecto es 300.0.
            poll_interval (float, optional): Segundos entre consultas. Por defecto es 5.0.

        Returns:
            FalabellaResponse: Response whose ``request_id`` is the feed id when
                ``wait=False``.
            FeedStatus: The finished feed when ``wait=True``.
        """
        params = {
            "Action": "ProductUpdate"
        }

        if wait:
            # Validate before sending: a write that fails afterwards would be retried.
            validate_wait_options(timeout, poll_interval)
        payload = _xml_payload(payload)
        response = unwrap(self.client.query('post', params=params, payload=payload))
        if wait:
            return self._wait_for_feed(response, "ProductUpdate", timeout, poll_interval)
        return response

    def remove(self, payload: ProductPayload, *, wait: bool = False, timeout: float = 300.0,
               poll_interval: float = 5.0) -> Union[FalabellaResponse, "FeedStatus"]:
        """Elimina productos de la plataforma.

        Args:
            payload (dict | list[dict] | str | bytes): Producto(s) a eliminar, por ejemplo
                ``{"SellerSku": "TP-1"}``, o XML.
            wait (bool, optional): Esperar a que el feed termine. Por defecto es False.
            timeout (float, optional): Segundos máximos de espera. Por defecto es 300.0.
            poll_interval (float, optional): Segundos entre consultas. Por defecto es 5.0.

        Returns:
            FalabellaResponse: Response whose ``request_id`` is the feed id when
                ``wait=False``.
            FeedStatus: The finished feed when ``wait=True``.
        """
        params = {
            "Action": "ProductRemove"
        }

        if wait:
            # Validate before sending: a write that fails afterwards would be retried.
            validate_wait_options(timeout, poll_interval)
        payload = _xml_payload(payload)
        response = unwrap(self.client.query('post', params=params, payload=payload))
        if wait:
            return self._wait_for_feed(response, "ProductRemove", timeout, poll_interval)
        return response

    def update_price_and_stock(self, items: Union[PriceStockUpdate,
                                                 Sequence[PriceStockUpdate]],
                               *, wait: bool = False, timeout: float = 300.0,
                               poll_interval: float = 5.0) -> Union[FalabellaResponse,
                                                                    "FeedStatus"]:
        """Update price and/or stock keeping any active special price.

        Reads the current state with one ``GetProducts`` call, then sends one
        ``ProductUpdate`` per call (fetched and written in the same call). Fields the
        caller sets win; when the current product has an active ``SpecialPrice`` and
        the caller did not set ``SpecialPrice``, the current special price and dates
        are re-sent. ``Price``, ``Stock`` and ``Status`` are never copied.

        There is a read-modify-write race: a change made in Seller Center between the
        read and the write can be overwritten. The API has no conditional writes.

        Args:
            items: One update or a list of updates (up to 50 per call).
            wait: Wait for the feed when True. Defaults to False.
            timeout: Maximum seconds to wait. Defaults to 300.0.
            poll_interval: Seconds between polls. Defaults to 5.0.

        Returns:
            FalabellaResponse: Write response when ``wait=False``.
            FeedStatus: Finished feed when ``wait=True``.

        Raises:
            ValueError: For invalid items, unknown SKUs, or invalid wait options.
                Validation happens before any write.
        """
        if isinstance(items, dict):
            items = [items]
        elif isinstance(items, (list, tuple)):
            items = list(items)
        else:
            raise ValueError("items must be a dict or a list of dicts")
        if not 1 <= len(items) <= 50:
            raise ValueError("items must contain between 1 and 50 products")

        seen = set()
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("each item must be a dict")
            seller_sku = item.get("SellerSku")
            if not isinstance(seller_sku, str) or not seller_sku.strip():
                raise ValueError("each item requires a non-empty SellerSku")
            if seller_sku in seen:
                raise ValueError(f"duplicate SellerSku: {seller_sku}")
            seen.add(seller_sku)
            if not any(field in item for field in _PRICE_STOCK_FIELDS):
                raise ValueError(
                    f"item {seller_sku} must set at least one of "
                    f"{', '.join(_PRICE_STOCK_FIELDS)}"
                )

        if wait:
            validate_wait_options(timeout, poll_interval)

        skus = [item["SellerSku"] for item in items]
        current_response = self.get(SkuSellerList=json.dumps(skus), limit=len(skus))
        current_by_sku = {
            product.get("SellerSku"): product
            for product in current_response.items
            if isinstance(product, dict)
        }
        missing = [sku for sku in skus if sku not in current_by_sku]
        if missing:
            raise ValueError(f"Unknown SellerSku: {', '.join(missing)}")

        operator_code = self.client.business_unit.lower()
        payloads = []
        for item in items:
            seller_sku = item["SellerSku"]
            current_unit = _find_business_unit(current_by_sku[seller_sku], operator_code)
            business_unit = {"OperatorCode": operator_code}
            for field in _PRICE_STOCK_FIELDS:
                if field in item:
                    business_unit[field] = item[field]
            if "SpecialPrice" not in item and current_unit.get("SpecialPrice"):
                for field in ("SpecialPrice", "SpecialFromDate", "SpecialToDate"):
                    if field not in item:
                        business_unit[field] = current_unit.get(field, "")
            payloads.append(
                {"SellerSku": seller_sku, "BusinessUnits": {"BusinessUnit": business_unit}}
            )

        return self.update(
            payloads, wait=wait, timeout=timeout, poll_interval=poll_interval
        )

    def brands(self) -> FalabellaResponse:
        """Busca las marcas de vendedor disponibles.

        Returns:
            FalabellaResponse: Brands in ``items`` (inner ``Brand`` dicts).
        """
        params = {
            "Action": "GetBrands"
        }

        return unwrap_collection(
            self.client.query('get', params=params), "Brands", item_key="Brand"
        )

    def get_category_tree(self) -> FalabellaResponse:
        """Obtiene la jerarquía completa de categorías de la plataforma.

        Returns:
            FalabellaResponse: Top-level categories in ``items``.
        """
        params = {
            "Action": "GetCategoryTree"
        }

        return unwrap_collection(
            self.client.query('get', params=params), "Categories", "Category"
        )

    def get_category_attributes(self, primary_category_id: int) -> FalabellaResponse:
        """Obtiene los atributos requeridos y opcionales asociados a una categoría específica.

        Args:
            primary_category_id (int): Identificador de la categoría principal.

        Returns:
            FalabellaResponse: Category attributes in ``items``.
        """
        params = {
            "Action": "GetCategoryAttributes",
            "PrimaryCategory": primary_category_id
        }

        return unwrap_collection(self.client.query('get', params=params), "Attribute")
