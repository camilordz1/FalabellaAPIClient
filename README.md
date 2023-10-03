# FalabellaAPIClient

Este módulo permite interactuar con el API de Linio y Falabella para leer, actualizar y crear productos, órdenes y datos de clientes. Este módulo es útil para integrar el API de Linio con otros sistemas.

## Instalación

Para instalar este módulo, ejecute el siguiente comando:

```bash
pip install FalabellaAPIClient
```

Uso básico
Para usar este módulo, primero debe obtener las credenciales de acceso al API de desde [Linio sellercenter](https://sellercenter.linio.com.co/), en la sección de configuración general > administrar usuarios ó en [falabella sellercenter](https://sellercenter.falabella.com/), en la sección de Mi cuenta > Integraciones

```python
from FalabellaAPIClient import Session, Products, Service, Orders
import json

# login
user = "email@example.com"
key = "_api_key_"

session = Session(user, key, "falabella")
service = Service()

# get a product

items = Products(service, session)

product_list = ["TP-19150"]

item = items.get(SkuSellerList=json.dumps(product_list))

print("product:", item)

# get orders

order = Orders(service, session)

print("order:", order.get(100513))
print("orderItems:", order.items(100513))

```

## Créditos

Camilo Andrés Rodriguez

## referencias

https://developers.falabella.com/

## Licencia

Este proyecto está bajo la Licencia [MIT].