import json
from typing import Any, Dict, List, Union
from FalabellaAPIClient.actions import Actions


class Shipments(Actions):
    """Operaciones relacionadas con los despachos y transportistas en la API de Falabella/Linio."""

    def __init__(self, service_or_client: Any = None, session: Any = None) -> None:
        """Inicializa el recurso de Envíos.

        Args:
            service_or_client (Any, optional): Instancia de FalabellaClient (nueva arquitectura)
                o Service (arquitectura heredada).
            session (Any, optional): Instancia de Session (solo para arquitectura heredada).
        """
        if session is not None:
            self.service = service_or_client
            self.session = session
            self._legacy = True
            super().__init__(None)
        else:
            super().__init__(service_or_client)
            self._legacy = False

    def get_providers(self) -> Dict[str, Any]:
        """Obtiene la lista de transportistas de envío activos disponibles para la cuenta.

        Returns:
            dict: Proveedores de envío.
        """
        params = {
            "Action": "GetShipmentProviders"
        }

        if getattr(self, '_legacy', False):
            return self.service.request(self.session, 'get', params)
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

        if getattr(self, '_legacy', False):
            return self.service.request(self.session, 'get', params)
        return self.client.query('get', params=params)
