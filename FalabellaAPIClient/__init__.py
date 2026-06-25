from FalabellaAPIClient.client import FalabellaClient, FalabellaAPIError
from FalabellaAPIClient.products import Products
from FalabellaAPIClient.orders import Orders
from FalabellaAPIClient.seller import Seller
from FalabellaAPIClient.shipments import Shipments

# Importaciones para compatibilidad heredada (Legacy)
from FalabellaAPIClient.session import Session
from FalabellaAPIClient.service import Service

__all__ = [
    'FalabellaClient',
    'FalabellaAPIError',
    'Products',
    'Orders',
    'Seller',
    'Shipments',
    'Session',
    'Service',
]
