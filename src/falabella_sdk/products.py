from typing import TYPE_CHECKING, Any

from falabella_sdk.actions import Actions
from falabella_sdk.responses import FalabellaResponse, unwrap, unwrap_collection

if TYPE_CHECKING:
    from falabella_sdk.client import FalabellaClient


class Products(Actions):
    """Operaciones relacionadas con el recurso de Productos en la API de Falabella."""

    def __init__(self, client: "FalabellaClient") -> None:
        """Initialize the resource with an authenticated client.

        Args:
            client (FalabellaClient): An initialized Falabella client.
        """
        super().__init__(client)

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

    def create(self, payload: Any) -> FalabellaResponse:
        """Crea nuevos productos en la plataforma.

        Args:
            payload (Any): Datos de los productos (usualmente una cadena XML con
                estructura de producto).

        Returns:
            FalabellaResponse: Response whose ``request_id`` is the feed id.
        """
        params = {
            "Action": "ProductCreate"
        }

        return unwrap(self.client.query('post', params=params, payload=payload))

    def update(self, payload: Any) -> FalabellaResponse:
        """Actualiza productos existentes.

        Args:
            payload (Any): Datos actualizados de los productos (estructura XML).

        Returns:
            FalabellaResponse: Response whose ``request_id`` is the feed id.
        """
        params = {
            "Action": "ProductUpdate"
        }

        return unwrap(self.client.query('post', params=params, payload=payload))

    def remove(self, payload: Any) -> FalabellaResponse:
        """Elimina productos de la plataforma.

        Args:
            payload (Any): Datos de identificación de los productos a eliminar.

        Returns:
            FalabellaResponse: Response whose ``request_id`` is the feed id.
        """
        params = {
            "Action": "ProductRemove"
        }

        return unwrap(self.client.query('post', params=params, payload=payload))

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
