# FalabellaAPIClient

Este módulo permite interactuar de manera sencilla y eficiente con la API de Falabella y Linio Seller Center para administrar productos, categorías, órdenes, despachos y datos del vendedor.

El cliente ha sido rediseñado utilizando una **arquitectura basada en composición y propiedades perezosas (lazy properties)** para ofrecer una interfaz unificada y moderna, manteniendo al mismo tiempo compatibilidad del 100% con integraciones previas.

---

## Instalación

Para instalar el módulo localmente o desde tu entorno de desarrollo, ejecuta:

```bash
pip install FalabellaAPIClient
```

O agrégalo a tu archivo `requirements.txt`:

```text
FalabellaAPIClient
```

---

## Uso Básico (Nueva Arquitectura)

La nueva arquitectura utiliza un único cliente (`FalabellaClient`) que gestiona internamente la sesión HTTP y la generación de firmas `HMAC-SHA256`. Los recursos se cargan dinámicamente como propiedades del cliente.

```python
import json
from FalabellaAPIClient import FalabellaClient, FalabellaAPIError

# Inicializar el cliente unificado
client = FalabellaClient(
    user="email@example.com",
    key="_api_key_",
    service="falabella",  # "falabella" 
    country="co"          # "co", "cl", "pe", "mx", etc.
)

# 1. Obtener información de un producto
try:
    product_list = ["TP-19150"]
    item = client.products.get(SkuSellerList=json.dumps(product_list))
    print("Producto obtenido:", item)
except FalabellaAPIError as e:
    print(f"Error al obtener el producto: {e.message} (Status: {e.status_code})")

# 2. Consultar órdenes
try:
    orders_list = client.orders.list(Limit=10)
    print("Últimas 10 órdenes:", orders_list)
    
    # Obtener ítems de una orden específica
    order_items = client.orders.items(order_id=100513)
    print("Ítems de la orden 100513:", order_items)
except FalabellaAPIError as e:
    print(f"Error con las órdenes: {e}")
```

---

## Timeouts and retries

`FalabellaClient` accepts keyword-only transport options:

```python
client = FalabellaClient(
    user="email@example.com",
    key="_api_key_",
    timeout=30.0,        # seconds per request
    max_retries=3,       # retries after the first attempt
    backoff_factor=1.0,  # exponential backoff base
)
```

Requests that were not processed are retried up to `1 + max_retries` attempts. Delays use a
numeric `Retry-After` header when present, otherwise `backoff_factor * 2 ** (attempt - 1)`, and
are capped at 60 seconds.

| Condition | GET | POST (writes) |
|---|---|---|
| HTTP 429 | retry | retry |
| `ErrorResponse` with `ErrorCode` `429` | retry | retry |
| HTTP 5xx | retry | no retry |
| `ConnectionError` / `Timeout` | retry | no retry |
| Any other error | no retry | no retry |

---

## Recursos Disponibles

El cliente `FalabellaClient` expone los siguientes recursos mediante propiedades perezosas:

### 1. `client.products` (Productos y Categorías)
*   `get(limit=1000, **kwargs)`: Obtiene información de productos utilizando el filtro `GetProducts`.
*   `create(payload)`: Crea nuevos productos enviando una estructura XML.
*   `update(payload)`: Actualiza productos existentes (estructura XML).
*   `remove(payload)`: Elimina productos de la plataforma.
*   `brands()`: Obtiene la lista de marcas asociadas del vendedor (`GetBrands`).
*   `get_category_tree()`: Recupera la jerarquía completa de categorías de la plataforma.
*   `get_category_attributes(primary_category_id)`: Retorna la lista de atributos y campos requeridos para una categoría específica.

### 2. `client.orders` (Órdenes de Venta)
*   `list(**kwargs)`: Obtiene la lista de órdenes (`GetOrders`).
*   `get(order_id, **kwargs)`: Obtiene detalles de una orden específica.
*   `items(order_id, template="JSON")`: Obtiene los ítems individuales de una orden.
*   `multiple_order_items(order_id_list, template="JSON")`: Obtiene ítems de una lista de órdenes.
*   **Transiciones de Estado de Despacho (Lifecycle):**
    *   `set_status_to_packed_by_marketplace(order_item_ids, shipping_provider, delivery_type)`
    *   `set_status_to_ready_to_ship(order_item_ids, shipping_provider, tracking_number, delivery_type)`
    *   `set_status_to_shipped(order_item_ids, tracking_number)`
    *   `set_status_to_delivered(order_item_ids)`
    *   `set_status_to_failed(order_item_ids, reason, reason_detail=None)`
    *   `set_status_to_cancelled(order_item_ids, reason, reason_detail=None)`

### 3. `client.seller` (Perfil del Vendedor)
*   `get()`: Obtiene el perfil de vendedor y el estado general de la cuenta (`GetSeller`).

### 4. `client.shipments` (Envíos y Documentación)
*   `get_providers()`: Obtiene el listado de transportistas disponibles (`GetShipmentProviders`).
*   `get_document(order_item_ids, document_type="shippingLabel")`: Descarga documentos en HTML/PDF como guías de despacho (`shippingLabel`), facturas (`invoice`) o manifiestos (`carrierManifest`).

---

## Compatibilidad Heredada (Legacy)

Si ya tienes implementaciones que usan la estructura original, estas **seguirán funcionando sin cambios**, aunque levantarán un `DeprecationWarning` sugiriendo la migración.

```python
from FalabellaAPIClient import Session, Products, Service, Orders
import json

# login legacy
user = "email@example.com"
key = "_api_key_"

session = Session(user, key, "falabella")
service = Service()

# Instanciar recursos pasando service y session individualmente
items = Products(service, session)
product_list = ["TP-19150"]
item = items.get(SkuSellerList=json.dumps(product_list))

order = Orders(service, session)
print("order:", order.get(100513))
```

---

## Development

Set up a virtual environment and install the runtime package together with the dev
dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt -e .
```

Run the test suite:

```bash
pytest
```

## Licencia

Este proyecto se encuentra bajo la Licencia [MIT](licence).