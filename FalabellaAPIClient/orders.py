import json
from typing import Any, Dict, List, Optional, Union
from FalabellaAPIClient.actions import Actions


class Orders(Actions):
    """Operaciones relacionadas con el recurso de Órdenes en la API de Falabella."""

    def __init__(self, client: "FalabellaClient") -> None:
        """Initialize the resource with an authenticated client.

        Args:
            client (FalabellaClient): An initialized Falabella client.
        """
        super().__init__(client)

    def list(self, **kwargs: Any) -> Dict[str, Any]:
        """Busca una lista de órdenes.

        Returns:
            dict: Lista de órdenes devuelta por el servidor.
        """
        params = {
            "Action": "GetOrders"
        }

        if kwargs:
            params.update(kwargs)

        return self.client.query('get', params=params)

    def get(self, order_id: Union[int, str], **kwargs: Any) -> Dict[str, Any]:
        """Busca la información detallada de una orden.

        Args:
            order_id (int o str): ID de la orden.

        Returns:
            dict: Información de la orden.
        """
        params = {
            "Action": "GetOrder",
            "OrderId": order_id
        }

        if kwargs:
            params.update(kwargs)

        return self.client.query('get', params=params)

    def items(self, order_id: Union[int, str], template: str = "JSON") -> Dict[str, Any]:
        """Busca los ítems individuales de una orden.

        Args:
            order_id (int o str): ID de la orden.
            template (str, optional): Formato de salida. Por defecto es "JSON".

        Returns:
            dict: Ítems de la orden.
        """
        params = {
            "Action": "GetOrderItems",
            "OrderId": order_id,
            "Format": template
        }

        return self.client.query('get', params=params)

    def multiple_order_items(self, order_id_list: Union[List[Union[int, str]], str],
                             template: str = "JSON") -> Dict[str, Any]:
        """Busca los ítems de una lista de órdenes.

        Args:
            order_id_list (list o str): Lista de IDs de órdenes (o string JSON serializado).
            template (str, optional): Formato de salida. Por defecto es "JSON".

        Returns:
            dict: Ítems de las órdenes consultadas.
        """
        if isinstance(order_id_list, (list, tuple)):
            order_id_list = json.dumps(order_id_list)

        params = {
            "Action": "GetMultipleOrderItems",
            "Format": template,
            "OrderIdList": order_id_list
        }

        return self.client.query('get', params=params)

    def set_status_to_packed_by_marketplace(self, order_item_ids: Union[List[Union[int, str]], str],
                                            shipping_provider: str, delivery_type: str,
                                            **kwargs: Any) -> Dict[str, Any]:
        """Marca los ítems de la orden como empacados (PackedByMarketplace).

        Args:
            order_item_ids (list o str): Lista de IDs de ítems de órdenes.
            shipping_provider (str): Nombre del proveedor de envío.
            delivery_type (str): Tipo de entrega (e.g., 'dropship').
            **kwargs: Parámetros adicionales.
        """
        if isinstance(order_item_ids, (list, tuple)):
            order_item_ids = json.dumps(order_item_ids)

        params = {
            "Action": "SetStatusToPackedByMarketplace",
            "OrderItemIds": order_item_ids,
            "ShippingProvider": shipping_provider,
            "DeliveryType": delivery_type
        }
        if kwargs:
            params.update(kwargs)

        return self.client.query('post', params=params)

    def set_status_to_ready_to_ship(self, order_item_ids: Union[List[Union[int, str]], str],
                                    shipping_provider: str, tracking_number: str, delivery_type: str,
                                    **kwargs: Any) -> Dict[str, Any]:
        """Marca los ítems de la orden como listos para despachar (ReadyToShip).

        Args:
            order_item_ids (list o str): Lista de IDs de ítems de órdenes.
            shipping_provider (str): Nombre del proveedor de envío.
            tracking_number (str): Número de seguimiento.
            delivery_type (str): Tipo de entrega.
            **kwargs: Parámetros adicionales.
        """
        if isinstance(order_item_ids, (list, tuple)):
            order_item_ids = json.dumps(order_item_ids)

        params = {
            "Action": "SetStatusToReadyToShip",
            "OrderItemIds": order_item_ids,
            "ShippingProvider": shipping_provider,
            "TrackingNumber": tracking_number,
            "DeliveryType": delivery_type
        }
        if kwargs:
            params.update(kwargs)

        return self.client.query('post', params=params)

    def set_status_to_shipped(self, order_item_ids: Union[List[Union[int, str]], str],
                              tracking_number: str, **kwargs: Any) -> Dict[str, Any]:
        """Marca los ítems de la orden como enviados (Shipped).

        Args:
            order_item_ids (list o str): Lista de IDs de ítems de órdenes.
            tracking_number (str): Número de seguimiento.
            **kwargs: Parámetros adicionales.
        """
        if isinstance(order_item_ids, (list, tuple)):
            order_item_ids = json.dumps(order_item_ids)

        params = {
            "Action": "SetStatusToShipped",
            "OrderItemIds": order_item_ids,
            "TrackingNumber": tracking_number
        }
        if kwargs:
            params.update(kwargs)

        return self.client.query('post', params=params)

    def set_status_to_delivered(self, order_item_ids: Union[List[Union[int, str]], str],
                                 **kwargs: Any) -> Dict[str, Any]:
        """Marca los ítems de la orden como entregados (Delivered).

        Args:
            order_item_ids (list o str): Lista de IDs de ítems de órdenes.
            **kwargs: Parámetros adicionales.
        """
        if isinstance(order_item_ids, (list, tuple)):
            order_item_ids = json.dumps(order_item_ids)

        params = {
            "Action": "SetStatusToDelivered",
            "OrderItemIds": order_item_ids
        }
        if kwargs:
            params.update(kwargs)

        return self.client.query('post', params=params)

    def set_status_to_failed(self, order_item_ids: Union[List[Union[int, str]], str],
                             reason: str, reason_detail: Optional[str] = None,
                             **kwargs: Any) -> Dict[str, Any]:
        """Marca los ítems de la orden como fallidos (Failed).

        Args:
            order_item_ids (list o str): Lista de IDs de ítems de órdenes.
            reason (str): Razón por la cual falló el despacho.
            reason_detail (str, optional): Detalle adicional sobre el fallo.
            **kwargs: Parámetros adicionales.
        """
        if isinstance(order_item_ids, (list, tuple)):
            order_item_ids = json.dumps(order_item_ids)

        params = {
            "Action": "SetStatusToFailed",
            "OrderItemIds": order_item_ids,
            "Reason": reason
        }
        if reason_detail:
            params["ReasonDetail"] = reason_detail
        if kwargs:
            params.update(kwargs)

        return self.client.query('post', params=params)

    def set_status_to_cancelled(self, order_item_ids: Union[List[Union[int, str]], str],
                                reason: str, reason_detail: Optional[str] = None,
                                **kwargs: Any) -> Dict[str, Any]:
        """Marca los ítems de la orden como cancelados (Cancelled).

        Args:
            order_item_ids (list o str): Lista de IDs de ítems de órdenes.
            reason (str): Razón por la cual se canceló la orden.
            reason_detail (str, optional): Detalle adicional sobre la cancelación.
            **kwargs: Parámetros adicionales.
        """
        if isinstance(order_item_ids, (list, tuple)):
            order_item_ids = json.dumps(order_item_ids)

        params = {
            "Action": "SetStatusToCancelled",
            "OrderItemIds": order_item_ids,
            "Reason": reason
        }
        if reason_detail:
            params["ReasonDetail"] = reason_detail
        if kwargs:
            params.update(kwargs)

        return self.client.query('post', params=params)
