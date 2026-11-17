from typing import TYPE_CHECKING

from falabella_sdk.actions import Actions
from falabella_sdk.responses import FalabellaResponse, unwrap

if TYPE_CHECKING:
    from falabella_sdk.client import FalabellaClient


class Seller(Actions):
    """Operaciones relacionadas con el perfil del Vendedor en la API de Falabella."""

    def __init__(self, client: "FalabellaClient") -> None:
        """Initialize the resource with an authenticated client.

        Args:
            client (FalabellaClient): An initialized Falabella client.
        """
        super().__init__(client)

    def get(self) -> FalabellaResponse:
        """Obtiene la información y estado de la cuenta del vendedor.

        Returns:
            FalabellaResponse: Seller profile in ``body``.
        """
        params = {
            "Action": "GetSellerByUser"
        }

        return unwrap(self.client.query('get', params=params))
