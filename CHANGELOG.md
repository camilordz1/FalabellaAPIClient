# Registro de cambios

Todos los cambios relevantes de `falabella-sdk` se documentan aquí. El formato sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa
[versionado semántico](https://semver.org/lang/es/). Mientras el SDK esté en versión alfa
(`1.0.0aN`), una versión nueva puede traer cambios incompatibles.

## [1.0.0a4] - 2026-11-17

### Añadido
- `products.create`, `update` y `remove` aceptan productos como diccionarios (o una lista de
  ellos), además del XML escrito a mano. Las claves son los nombres de la API (`SellerSku`,
  `BusinessUnits`, `ProductData`…). `None` omite un campo y `""` lo vacía.
- `to_xml(...)` y los tipos `Product`, `BusinessUnit`, `BusinessUnits` y `PriceStockUpdate`
  (`TypedDict`, sin dependencias nuevas).
- `products.update_price_and_stock(items, wait=False)`: actualiza precio, stock, estado y oferta de
  hasta 50 SKU con una lectura y una escritura. Conserva la oferta vigente cuando solo cambias
  otros campos; `SpecialPrice: ""` la quita.

### Corregido / validaciones
- El XML se escapa siempre; la descripción del producto va en `CDATA` para conservar su HTML.
- Se rechazan antes de enviar: caracteres no permitidos en XML, `SellerSku` vacío, `nan`/`inf`,
  precios o stock de 10^15 o más, y tipos de payload no soportados. Los números se escriben sin
  notación científica.
- `update_price_and_stock` no reenvía una oferta vencida (según la hora de la unidad de negocio) y
  falla antes de escribir si un `SpecialPrice` quedaría sin fechas o no sería menor que el `Price`.

## [1.0.0a3] - 2026-11-17

### Añadido
- `client.feeds`: `list()` devuelve los feeds recientes y `status(feed_id)` devuelve un
  `FeedStatus` con el estado, los conteos (`total_records`, `processed_records`,
  `failed_records`) y los errores por SKU (`FeedError`: `seller_sku`, `code`, `message`).
- `client.feeds.wait(feed_id, timeout=300, poll_interval=5)`: espera a que el feed termine, con un
  tiempo máximo.
- `wait=True` en `products.create`, `update` y `remove`: espera el feed y devuelve su
  `FeedStatus`, o lanza `FalabellaFeedError` si hubo registros fallidos o el feed no terminó en
  `Finished`.
- `FalabellaFeedError` y `FalabellaFeedTimeout`, con `feed_status` y `errors`.
- `FalabellaAPIError.feed_id`: cuando falla la espera de una escritura que ya se envió, el error
  incluye el id del feed para consultarlo más tarde en lugar de reenviar la escritura.
- Ejemplo `examples/basic_usage.py` actualizado a `FalabellaResponse` y feeds.

### Corregido
- Las opciones de espera (`timeout`, `poll_interval`) se validan antes de enviar la escritura, para
  no enviarla si son inválidas.
- Un feed se considera terminado cuando su estado no es `Queued` ni `Processing`, de modo que un
  estado final desconocido no deja la espera bloqueada.

## [1.0.0a2] - 2026-11-17

### Cambiado (incompatible)
- Los métodos de recursos devuelven `FalabellaResponse` en lugar del diccionario crudo. Las
  colecciones están siempre en `.items` como lista (aunque haya un solo elemento o ninguno); la
  respuesta original sigue en `.raw`. Ver **Cambios incompatibles** en el README.

### Añadido
- `FalabellaResponse` con `items`, `head`, `body`, `raw`, `request_id`, `request_action`,
  `response_type` y `total_count`.

### Corregido
- `seller.get()` usa la acción `GetSellerByUser`; `GetSeller` no existe en la API.
- `products.brands()` acepta las dos formas en que la API entrega las marcas.

## [1.0.0a1] - 2026-11-16

Primera versión con el nombre `falabella-sdk` (antes `FalabellaAPIClient`).

### Cambiado (incompatible)
- El paquete se renombró a `falabella-sdk` (importación `falabella_sdk`).
- Se eliminaron Linio, las clases heredadas `Session` y `Service` y los parámetros `service` y
  `country`.
- Requiere Python 3.10 o superior.

### Añadido
- Encabezado `User-Agent` exigido por Falabella, construido a partir de `seller_id`,
  `integration_type` y `business_unit`.
- Tiempo de espera, reintentos acotados con `Retry-After` y `FalabellaAPIError` con
  `error_code`, `error_type`, `action` y `details`.

### Corregido
- La firma codifica los espacios como `%20`: antes cualquier parámetro con espacios fallaba con
  `E007: Signature mismatch`.

[1.0.0a4]: https://pypi.org/project/falabella-sdk/1.0.0a4/
[1.0.0a3]: https://pypi.org/project/falabella-sdk/1.0.0a3/
[1.0.0a2]: https://pypi.org/project/falabella-sdk/1.0.0a2/
[1.0.0a1]: https://pypi.org/project/falabella-sdk/1.0.0a1/
