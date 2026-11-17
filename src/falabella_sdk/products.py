from typing import TYPE_CHECKING, Any, Union

from falabella_sdk.actions import Actions
from falabella_sdk.client import FalabellaAPIError, FalabellaFeedError
from falabella_sdk.feeds import validate_wait_options
from falabella_sdk.responses import FalabellaResponse, unwrap, unwrap_collection

if TYPE_CHECKING:
    from falabella_sdk.client import FalabellaClient
    from falabella_sdk.feeds import FeedStatus


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
            raise FalabellaFeedError(feed_status)
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

    def create(self, payload: Any, *, wait: bool = False, timeout: float = 300.0,
               poll_interval: float = 5.0) -> Union[FalabellaResponse, "FeedStatus"]:
        """Crea nuevos productos en la plataforma.

        Args:
            payload (Any): Datos de los productos (usualmente una cadena XML con
                estructura de producto).
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
        response = unwrap(self.client.query('post', params=params, payload=payload))
        if wait:
            return self._wait_for_feed(response, "ProductCreate", timeout, poll_interval)
        return response

    def update(self, payload: Any, *, wait: bool = False, timeout: float = 300.0,
               poll_interval: float = 5.0) -> Union[FalabellaResponse, "FeedStatus"]:
        """Actualiza productos existentes.

        Args:
            payload (Any): Datos actualizados de los productos (estructura XML).
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
        response = unwrap(self.client.query('post', params=params, payload=payload))
        if wait:
            return self._wait_for_feed(response, "ProductUpdate", timeout, poll_interval)
        return response

    def remove(self, payload: Any, *, wait: bool = False, timeout: float = 300.0,
               poll_interval: float = 5.0) -> Union[FalabellaResponse, "FeedStatus"]:
        """Elimina productos de la plataforma.

        Args:
            payload (Any): Datos de identificación de los productos a eliminar.
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
        response = unwrap(self.client.query('post', params=params, payload=payload))
        if wait:
            return self._wait_for_feed(response, "ProductRemove", timeout, poll_interval)
        return response

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
