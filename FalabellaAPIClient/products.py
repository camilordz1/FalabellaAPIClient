from typing import Any, Dict, TYPE_CHECKING
from FalabellaAPIClient.actions import Actions

if TYPE_CHECKING:
    from FalabellaAPIClient.client import FalabellaClient


class Products(Actions):
    """Operaciones relacionadas con el recurso de Productos en la API de Falabella."""

    def __init__(self, client: "FalabellaClient") -> None:
        """Initialize the resource with an authenticated client.

        Args:
            client (FalabellaClient): An initialized Falabella client.
        """
        super().__init__(client)

    def get(self, limit: int = 1000, **kwargs: Any) -> Dict[str, Any]:
        """Obtiene información de uno o varios productos.

        Args:
            limit (int, optional): Número máximo de resultados (1 a 1000). Por defecto es 1000.
            **kwargs: Filtros adicionales (e.g., SkuSellerList, Search, CreatedAfter, etc.).

        Returns:
            dict: Información de los productos devuelta por el servidor.
        """
        params = {
            "Action": "GetProducts",
            "Limit": limit
        }

        if kwargs:
            params.update(kwargs)

        return self.client.query('get', params=params)

    def create(self, payload: Any) -> Dict[str, Any]:
        """Crea nuevos productos en la plataforma.

        Args:
            payload (Any): Datos de los productos (usualmente una cadena XML con estructura de producto).

        Returns:
            dict: Respuesta del servidor a la operación de creación.
        """
        params = {
            "Action": "ProductCreate"
        }

        return self.client.query('post', params=params, payload=payload)

    def update(self, payload: Any) -> Dict[str, Any]:
        """Actualiza productos existentes.

        Args:
            payload (Any): Datos actualizados de los productos (estructura XML).

        Returns:
            dict: Respuesta del servidor a la operación de actualización.
        """
        params = {
            "Action": "ProductUpdate"
        }

        return self.client.query('post', params=params, payload=payload)

    def remove(self, payload: Any) -> Dict[str, Any]:
        """Elimina productos de la plataforma.

        Args:
            payload (Any): Datos de identificación de los productos a eliminar.

        Returns:
            dict: Respuesta del servidor a la operación de eliminación.
        """
        params = {
            "Action": "ProductRemove"
        }

        return self.client.query('post', params=params, payload=payload)

    def brands(self) -> Dict[str, Any]:
        """Busca las marcas de vendedor disponibles.

        Returns:
            dict: Marcas asociadas al vendedor.
        """
        params = {
            "Action": "GetBrands"
        }

        return self.client.query('get', params=params)

    def get_category_tree(self) -> Dict[str, Any]:
        """Obtiene la jerarquía completa de categorías de la plataforma.

        Returns:
            dict: Árbol de categorías devuelto por la API.
        """
        params = {
            "Action": "GetCategoryTree"
        }

        return self.client.query('get', params=params)

    def get_category_attributes(self, primary_category_id: int) -> Dict[str, Any]:
        """Obtiene los atributos requeridos y opcionales asociados a una categoría específica.

        Args:
            primary_category_id (int): Identificador de la categoría principal.

        Returns:
            dict: Lista de atributos y sus tipos.
        """
        params = {
            "Action": "GetCategoryAttributes",
            "PrimaryCategory": primary_category_id
        }

        return self.client.query('get', params=params)
