from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from falabella_sdk.client import FalabellaClient


class Actions:
    """Clase base para todos los recursos de la API de Falabella Seller Center."""

    def __init__(self, client: Optional['FalabellaClient'] = None) -> None:
        """Inicializa el recurso con una referencia al cliente unificado.

        Args:
            client (FalabellaClient, optional): Instancia del cliente de Falabella.
        """
        self._client = client

    @property
    def client(self) -> 'FalabellaClient':
        """Obtiene la instancia del cliente para este recurso.

        Raises:
            ValueError: Si el cliente no ha sido inicializado.
        """
        if self._client is not None:
            return self._client
        raise ValueError("El cliente no ha sido inicializado para este recurso.")

    @client.setter
    def client(self, value: Optional['FalabellaClient']) -> None:
        """Establece la instancia del cliente para este recurso."""
        self._client = value
