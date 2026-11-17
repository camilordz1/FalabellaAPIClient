# FalabellaAPIClient (obsoleto)

> **Este paquete ahora se llama [`falabella-sdk`](https://pypi.org/project/falabella-sdk/).**
> `FalabellaAPIClient` ya no recibirá actualizaciones.

```bash
pip uninstall FalabellaAPIClient
pip install falabella-sdk
```

```python
# Antes
from FalabellaAPIClient import FalabellaClient

# Después
from falabella_sdk import FalabellaClient
```

La versión 0.2.0 de `FalabellaAPIClient` solo instala `falabella-sdk`, reexporta sus nombres y
emite un `FutureWarning` al importarse. `falabella-sdk` trae cambios incompatibles (se eliminaron
Linio y las clases heredadas `Session` y `Service`); consulta la sección **Cambios incompatibles**
de su [README](https://github.com/camilordz1/FalabellaAPIClient#cambios-incompatibles).

Si necesitas la API anterior, fija la versión `FalabellaAPIClient==0.1.1`.

SDK **no oficial**: este proyecto no está afiliado ni respaldado por Falabella.
