# falabella-sdk

[![CI](https://github.com/camilordz1/FalabellaAPIClient/actions/workflows/ci.yml/badge.svg)](https://github.com/camilordz1/FalabellaAPIClient/actions/workflows/ci.yml)

**SDK no oficial** de Python para la API de Falabella Seller Center. Este proyecto no está afiliado ni respaldado por Falabella.

Este módulo permite interactuar de manera sencilla y eficiente con la API de Falabella Seller Center para administrar productos, categorías, órdenes, despachos y datos del vendedor. El cliente utiliza una arquitectura basada en composición y propiedades perezosas (lazy properties) para ofrecer una interfaz unificada y moderna. La versión anterior y el soporte de Linio se eliminaron; consulta la sección **Cambios incompatibles** para migrar.

---

## Instalación

```bash
pip install falabella-sdk
```

Requiere Python 3.10+.

---

## Uso básico

La arquitectura actual utiliza un único cliente (`FalabellaClient`) que gestiona internamente la sesión HTTP y la generación de firmas `HMAC-SHA256`. Los recursos se cargan dinámicamente como propiedades del cliente.

```python
import json
from falabella_sdk import FalabellaClient, FalabellaAPIError

# Inicializar el cliente unificado
client = FalabellaClient(
    user="email@example.com",
    key="_api_key_",
    seller_id="ABC123",   # seller id que aparece en Seller Center en "Mi cuenta"
    business_unit="FACO", # "FACL" (Chile), "FACO" (Colombia), "FAPE" (Perú)
    integration_type="PROPIA",  # nombre del integrador si no eres el vendedor
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

Falabella exige enviar un encabezado `User-Agent` con el formato
`SELLER_ID/TECHNOLOGY/TECHNOLOGY_VERSION/INTEGRATION_TYPE/BUSINESS_UNIT_CODE`
(por ejemplo, `ABC123/Python/3.12.1/PROPIA/FACO`). El cliente lo construye a partir de `seller_id`,
`integration_type` y `business_unit`; el seller id aparece en Seller Center en "Mi cuenta".
`seller_id` es opcional por ahora: si falta, el cliente emite un `UserWarning` y no envía el
`User-Agent` de Falabella. Será obligatorio en la próxima versión mayor.

---

## Tiempos de espera y reintentos

`FalabellaClient` acepta las siguientes opciones de transporte como argumentos de solo palabra clave:

```python
client = FalabellaClient(
    user="email@example.com",
    key="_api_key_",
    timeout=30.0,        # segundos por petición
    max_retries=3,       # reintentos después del primer intento
    backoff_factor=1.0,  # base del backoff exponencial
)
```

Las peticiones que no fueron procesadas se reintentan hasta `1 + max_retries` veces. Los tiempos de
espera usan el encabezado `Retry-After` cuando es numérico; de lo contrario, aplican
`backoff_factor * 2 ** (attempt - 1)`, con un máximo de 60 segundos.

| Condición | GET | POST (escrituras) |
|---|---|---|
| HTTP 429 | reintentar | reintentar |
| `ErrorResponse` con `ErrorCode` `429` | reintentar | reintentar |
| HTTP 5xx | reintentar | no reintentar |
| `ConnectionError` / `Timeout` | reintentar | no reintentar |
| Cualquier otro error | no reintentar | no reintentar |

`payload` debe ser `None`, `str` o `bytes` (XML); otros tipos lanzan `TypeError` antes de enviar la
petición.

---

## Recursos disponibles

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

## Cambios incompatibles

- Python 3.9 ya no es compatible; la versión mínima es Python 3.10.
- El paquete se renombró de `FalabellaAPIClient` a `falabella-sdk` (importación `falabella_sdk`).

  ```python
  # Antes
  from FalabellaAPIClient import FalabellaClient

  # Después
  from falabella_sdk import FalabellaClient
  ```

- Se eliminó el soporte de Linio; el cliente siempre apunta a `https://sellercenter-api.falabella.com`.
- Se eliminaron los parámetros `service` y `country` del constructor.
- Se eliminaron las clases heredadas `Session` y `Service`. Usa `FalabellaClient` y sus propiedades
  de recursos (`client.products`, `client.orders`, `client.seller`, `client.shipments`) en su lugar.

```python
# Antes
session = Session(user, key, "falabella")
service = Service()
items = Products(service, session)

# Después
from falabella_sdk import FalabellaClient

client = FalabellaClient(user=user, key=key, seller_id="ABC123")
items = client.products
```

Consulta `examples/basic_usage.py` para ver un script completo controlado por variables de entorno.

---

## Desarrollo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
```

## Licencia

Este proyecto se encuentra bajo la Licencia [MIT](LICENSE).
