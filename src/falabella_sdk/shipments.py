import json
from typing import TYPE_CHECKING, List, Union

from falabella_sdk.actions import Actions
from falabella_sdk.responses import FalabellaResponse, unwrap, unwrap_collection

if TYPE_CHECKING:
    from falabella_sdk.client import FalabellaClient


class Shipments(Actions):
    """Operaciones relacionadas con los despachos y transportistas en la API de Falabella."""

    def __init__(self, client: "FalabellaClient") -> None:
        """Initialize the resource with an authenticated client.

        Args:
            client (FalabellaClient): An initialized Falabella client.
        """
        super().__init__(client)

    def get_providers(self) -> FalabellaResponse:
        """Obtiene la lista de transportistas de envío activos disponibles para la cuenta.

        Returns:
            FalabellaResponse: Providers in ``items``.
        """
        params = {
            "Action": "GetShipmentProviders"
        }

        return unwrap_collection(
            self.client.query('get', params=params),
            "ShipmentProviders",
            "ShipmentProvider",
        )

    def get_document(self, order_item_ids: Union[List[Union[int, str]], str],
                     document_type: str = "shippingLabel") -> FalabellaResponse:
        """Obtiene un documento de despacho (e.g., etiqueta de envío, manifiesto,
        factura) para ciertos ítems.

        Args:
            order_item_ids (list o str): Lista de IDs de ítems de órdenes.
            document_type (str, optional): Tipo de documento. Por defecto es "shippingLabel".
                Opciones comunes: "shippingLabel", "invoice", "carrierManifest".

        Returns:
            FalabellaResponse: Document response in ``body``.
        """
        if isinstance(order_item_ids, (list, tuple)):
            order_item_ids = json.dumps(order_item_ids)

        params = {
            "Action": "GetDocument",
            "OrderItemIds": order_item_ids,
            "DocumentType": document_type
        }

        return unwrap(self.client.query('get', params=params))
