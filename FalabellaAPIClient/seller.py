from typing import Any, Dict, TYPE_CHECKING
from FalabellaAPIClient.actions import Actions

if TYPE_CHECKING:
    from FalabellaAPIClient.client import FalabellaClient


class Seller(Actions):
    """Operaciones relacionadas con el perfil del Vendedor en la API de Falabella."""

    def __init__(self, client: "FalabellaClient") -> None:
        """Initialize the resource with an authenticated client.

        Args:
            client (FalabellaClient): An initialized Falabella client.
        """
        super().__init__(client)

    def get(self) -> Dict[str, Any]:
        """Obtiene la información y estado de la cuenta del vendedor.

        Returns:
            dict: Datos del perfil del vendedor.
        """
        params = {
            "Action": "GetSeller"
        }

        return self.client.query('get', params=params)
