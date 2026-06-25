from typing import Any, Dict, Optional
from FalabellaAPIClient.actions import Actions


class Products(Actions):
    """Operaciones relacionadas con el recurso de Productos en la API de Falabella/Linio."""

    def __init__(self, service_or_client: Any = None, session: Any = None) -> None:
        """Inicializa el recurso de Productos.

        Args:
            service_or_client (Any, optional): Instancia de FalabellaClient (nueva arquitectura)
                o Service (arquitectura heredada).
            session (Any, optional): Instancia de Session (solo para arquitectura heredada).
        """
        if session is not None:
            # Compatibilidad con arquitectura heredada
            self.service = service_or_client
            self.session = session
            self._legacy = True
            super().__init__(None)
        else:
            # Nueva arquitectura basada en composición
            super().__init__(service_or_client)
            self._legacy = False

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

        if getattr(self, '_legacy', False):
            return self.service.request(self.session, 'get', params)
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

        if getattr(self, '_legacy', False):
            return self.service.request(self.session, 'post', params, payload)
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

        if getattr(self, '_legacy', False):
            return self.service.request(self.session, 'post', params, payload)
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

        if getattr(self, '_legacy', False):
            return self.service.request(self.session, 'post', params, payload)
        return self.client.query('post', params=params, payload=payload)

    def brands(self) -> Dict[str, Any]:
        """Busca las marcas de vendedor disponibles.

        Returns:
            dict: Marcas asociadas al vendedor.
        """
        params = {
            "Action": "GetBrands"
        }

        if getattr(self, '_legacy', False):
            return self.service.request(self.session, 'get', params)
        return self.client.query('get', params=params)

    def get_category_tree(self) -> Dict[str, Any]:
        """Obtiene la jerarquía completa de categorías de la plataforma.

        Returns:
            dict: Árbol de categorías devuelto por la API.
        """
        params = {
            "Action": "GetCategoryTree"
        }

        if getattr(self, '_legacy', False):
            return self.service.request(self.session, 'get', params)
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

        if getattr(self, '_legacy', False):
            return self.service.request(self.session, 'get', params)
        return self.client.query('get', params=params)
