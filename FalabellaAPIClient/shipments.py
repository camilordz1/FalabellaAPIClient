import json
from typing import Any, Dict, List, Union, TYPE_CHECKING
from FalabellaAPIClient.actions import Actions

if TYPE_CHECKING:
    from FalabellaAPIClient.client import FalabellaClient


class Shipments(Actions):
    """Operaciones relacionadas con los despachos y transportistas en la API de Falabella."""

    def __init__(self, client: "FalabellaClient") -> None:
        """Initialize the resource with an authenticated client.

        Args:
            client (FalabellaClient): An initialized Falabella client.
        """
        super().__init__(client)

    def get_providers(self) -> Dict[str, Any]:
        """Obtiene la lista de transportistas de envío activos disponibles para la cuenta.

        Returns:
            dict: Proveedores de envío.
        """
        params = {
            "Action": "GetShipmentProviders"
        }

        return self.client.query('get', params=params)

    def get_document(self, order_item_ids: Union[List[Union[int, str]], str],
                     document_type: str = "shippingLabel") -> Dict[str, Any]:
        """Obtiene un documento de despacho (e.g., etiqueta de envío, manifiesto, factura) para ciertos ítems.

        Args:
            order_item_ids (list o str): Lista de IDs de ítems de órdenes.
            document_type (str, optional): Tipo de documento. Por defecto es "shippingLabel".
                Opciones comunes: "shippingLabel", "invoice", "carrierManifest".

        Returns:
            dict: El documento codificado (a menudo en HTML/PDF dentro del campo 'Document' o en base64).
        """
        if isinstance(order_item_ids, (list, tuple)):
            order_item_ids = json.dumps(order_item_ids)

        params = {
            "Action": "GetDocument",
            "OrderItemIds": order_item_ids,
            "DocumentType": document_type
        }

        return self.client.query('get', params=params)
