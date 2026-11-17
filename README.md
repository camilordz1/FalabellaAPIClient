# falabella-sdk

[![CI](https://github.com/camilordz1/falabella-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/camilordz1/falabella-sdk/actions/workflows/ci.yml)

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
    respuesta = client.products.get(SkuSellerList=json.dumps(product_list))
    print("Productos obtenidos:", respuesta.items)
except FalabellaAPIError as e:
    print(f"Error al obtener el producto: {e.message} (Status: {e.status_code})")

# 2. Consultar órdenes
try:
    respuesta = client.orders.list(Limit=10)
    print("Últimas 10 órdenes:", respuesta.items)
    
    # Obtener ítems de una orden específica
    items = client.orders.items(order_id=100513)
    print("Ítems de la orden 100513:", items.items)
except FalabellaAPIError as e:
    print(f"Error con las órdenes: {e}")
```

## Respuestas

Los métodos de recursos devuelven un `FalabellaResponse`:

- `items`: lista de elementos de la colección (`[]` si no hay elementos).
- `total_count`: `int` o `None`, tomado de `Head.TotalCount`.
- `request_id`: id de la petición; en las escrituras es el id del feed.
- `request_action` y `response_type`: metadatos de `Head`.
- `head`, `body` y `raw`: encabezado, cuerpo sin la envoltura y respuesta original.

| Método | Contenido de `items` |
|---|---|
| `client.products.get` | productos |
| `client.products.brands` | marcas (diccionarios internos `Brand`) |
| `client.products.get_category_tree` | categorías de primer nivel |
| `client.products.get_category_attributes` | atributos de categoría |
| `client.orders.list`, `get`, `multiple_order_items` | órdenes |
| `client.orders.items` | ítems de órdenes |
| `client.shipments.get_providers` | transportistas |

Los métodos que no devuelven colecciones (`products.create`/`update`/`remove`,
`orders.set_status_to_*`, `seller.get` y `shipments.get_document`) exponen los datos en `body`,
`request_id` y el resto de propiedades de `FalabellaResponse`.

Falabella exige enviar un encabezado `User-Agent` con el formato
`SELLER_ID/TECHNOLOGY/TECHNOLOGY_VERSION/INTEGRATION_TYPE/BUSINESS_UNIT_CODE`
(por ejemplo, `ABC123/Python/3.12.1/PROPIA/FACO`). El cliente lo construye a partir de `seller_id`,
`integration_type` y `business_unit`; el seller id aparece en Seller Center en "Mi cuenta".
`seller_id` es opcional por ahora: si falta, el cliente emite un `UserWarning` y no envía el
`User-Agent` de Falabella. Será obligatorio en la próxima versión mayor.

---

## Feeds

Las operaciones de escritura (`products.create`, `products.update`, `products.remove`, etc.) son
asíncronas: la respuesta trae un id de feed en `request_id` y Falabella procesa el feed después.
Usa `client.feeds.status(...)` para consultar cómo terminó:

```python
r = client.products.update(xml)
estado = client.feeds.status(r.request_id)
print(estado.status)          # "Finished", "Processing", ...
print(estado.failed_records)  # conteo convertido a número

for error in estado.errors:
    print(error.seller_sku, error.message)

recientes = client.feeds.list()
print(recientes.items)
```

`FeedStatus` expone `is_done` (el feed ya terminó) y `has_errors` (tuvo fallas), además de
`errors` y `warnings` con `seller_sku`, `code` y `message` por registro.

### Esperar el resultado

`products.create`, `products.update` y `products.remove` aceptan `wait=True` para esperar el feed:

```python
from falabella_sdk import FalabellaFeedError

try:
    estado = client.products.update(xml, wait=True, timeout=120)
    print("OK", estado.processed_records)
except FalabellaFeedError as error:
    for detalle in error.errors:
        print(detalle.seller_sku, detalle.message)
```

`timeout` (300 s por defecto) es el tiempo máximo total y `poll_interval` (5 s) la espera entre
consultas. Si se agota el tiempo se lanza `FalabellaFeedTimeout`, que conserva el último estado
consultado. Un feed `Finished` puede tener registros fallidos: en ese caso `wait=True` lanza
`FalabellaFeedError` con la lista de errores. Con `wait=False` (el valor por defecto) el método
devuelve el `FalabellaResponse` de siempre.

Si la espera falla (tiempo agotado, error de red o de la API), la escritura ya se envió: el error
incluye `feed_id` para que puedas consultar el feed más tarde con `client.feeds.status(e.feed_id)`
en lugar de reenviar la escritura.

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
*   `create(payload)`: Crea nuevos productos enviando un diccionario, una lista de diccionarios o XML.
*   `update(payload)`: Actualiza productos existentes (diccionario, lista o XML).
*   `remove(payload)`: Elimina productos de la plataforma (diccionario, lista o XML).
*   `brands()`: Obtiene la lista de marcas asociadas del vendedor (`GetBrands`).
*   `get_category_tree()`: Recupera la jerarquía completa de categorías de la plataforma.
*   `get_category_attributes(primary_category_id)`: Retorna la lista de atributos y campos requeridos para una categoría específica.

#### Enviar productos como diccionarios

`create`, `update` y `remove` aceptan un diccionario (o una lista de diccionarios) con los nombres
exactos de la API; las cadenas XML también siguen funcionando.

```python
from decimal import Decimal

client.products.update(
    {
        "SellerSku": "TP-10490",
        "Name": "Taladro",
        "BusinessUnits": {
            "BusinessUnit": {
                "OperatorCode": "faco",
                "Price": Decimal("310000.00"),
                "Stock": 5,
            }
        },
    },
    wait=True,
)
```

Envía los precios como `Decimal` o `str` para conservar los decimales exactos. Un valor `None`
omite el campo y `""` lo envía vacío (por ejemplo, para limpiar `SpecialPrice`).

#### Actualizar precio y stock sin perder la oferta

`update_price_and_stock(items, wait=...)` lee el estado actual de los SKU con un solo
`GetProducts`, arma un único `ProductUpdate` y conserva la oferta vigente (`SpecialPrice` y sus
fechas) cuando solo cambias stock u otros campos. Acepta hasta 50 SKU por llamada.

```python
from decimal import Decimal

client.products.update_price_and_stock(
    [
        {"SellerSku": "TP-10490", "Stock": 12},           # conserva la oferta vigente
        {"SellerSku": "TP-13027", "Price": Decimal("89900.00")},
        {"SellerSku": "TP-18545", "SpecialPrice": ""},    # quita la oferta
    ],
    wait=True,
)
```

El `OperatorCode` sale del `business_unit` del cliente (por ejemplo, `FACO` -> `faco`).
La validación ocurre antes de escribir: SKUs duplicados o inexistentes, más de 50 elementos u
opciones de espera inválidas fallan sin enviar el update. Entre la lectura y la escritura hay una
carrera: si la oferta cambia en Seller Center en ese instante, este update puede pisarla (la API
no ofrece escrituras condicionales).

Una oferta vencida (`SpecialToDate` anterior a hoy) no se vuelve a enviar. Si el resultado dejaría
un `SpecialPrice` igual o mayor que el `Price` (por ejemplo, al bajar el precio por debajo de la
oferta vigente), el método falla antes de escribir: cambia también `SpecialPrice` o quita la oferta
con `""`.

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
*   `get()`: Obtiene el perfil de vendedor y el estado general de la cuenta (`GetSellerByUser`).

### 4. `client.shipments` (Envíos y Documentación)
*   `get_providers()`: Obtiene el listado de transportistas disponibles (`GetShipmentProviders`).
*   `get_document(order_item_ids, document_type="shippingLabel")`: Descarga documentos en HTML/PDF como guías de despacho (`shippingLabel`), facturas (`invoice`) o manifiestos (`carrierManifest`).

### 5. `client.feeds` (Feeds asíncronos)
*   `list()`: Obtiene los feeds recientes (`FeedList`).
*   `status(feed_id)`: Obtiene el estado tipado de un feed (`FeedStatus`), con conteos, errores y advertencias.

---

## Cambios incompatibles

Consulta el [registro de cambios](CHANGELOG.md) para ver qué cambió en cada versión.

- Python 3.9 ya no es compatible; la versión mínima es Python 3.10.
- Los métodos de recursos ahora devuelven `FalabellaResponse` en lugar del diccionario crudo; la
  respuesta original sigue disponible en `.raw` y los elementos de colección están en `.items`.

  ```python
  # Antes
  productos = client.products.get()["SuccessResponse"]["Body"]["Products"]["Product"]

  # Después
  respuesta = client.products.get()
  productos = respuesta.items      # siempre una lista
  total = respuesta.total_count    # int o None
  ```

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
