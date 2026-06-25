import warnings
from requests import request as rq


class Service:
    """Clase heredada (Legacy) para ejecutar peticiones HTTP.

    Se recomienda migrar al uso de FalabellaClient.
    """

    def request(self, session: object, method: str, params: dict = {},
                payload: dict = {}, headers: dict = {}) -> dict | None:
        """Método de petición heredado.

        Args:
            session (object): Objeto de sesión (Session).
            method (str): Método HTTP (GET, POST).
            params (dict, optional): Parámetros.
            payload (dict, optional): Datos.
            headers (dict, optional): Cabeceras.

        Returns:
            dict | None: Respuesta del servidor o None.
        """
        warnings.warn(
            "La clase 'Service' es obsoleta. Use 'FalabellaClient' en su lugar.",
            DeprecationWarning,
            stacklevel=2
        )
        response = rq(method,
                      session.url,
                      data=payload,
                      params=session.signature(params),
                      headers=headers)

        if response.status_code == 200:
            return response.json()

        return None
