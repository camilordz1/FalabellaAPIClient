import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from hmac import HMAC
from urllib import parse
from hashlib import sha256

logger = logging.getLogger("falabella")


class FalabellaAPIError(Exception):
    """Excepción lanzada ante errores en las respuestas de la API de Falabella."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FalabellaClient:
    """Cliente unificado para interactuar con la API de Falabella y Linio Seller Center."""

    def __init__(self, user: str, key: str, service: str = "falabella", country: str = "co") -> None:
        """Inicializa el cliente de Falabella.

        Args:
            user (str): Correo electrónico del usuario (UserID).
            key (str): Llave API (API Key).
            service (str, optional): Servicio a usar ('falabella' o 'linio'). Por defecto es 'falabella'.
            country (str, optional): Código del país. Por defecto es 'co'.
        """
        self.user = user
        self.key = key
        self.service = service.lower()
        self.country = country.lower()

        # Configurar URL base
        if self.service == "falabella":
            self.url = "https://sellercenter-api.falabella.com"
        else:
            self.url = f"https://sellercenter-api.linio.com.{self.country}"

        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    @property
    def products(self) -> 'Products':
        """Acceso a operaciones del recurso Productos."""
        if not hasattr(self, '_products'):
            from FalabellaAPIClient.products import Products
            self._products = Products(self)
        return self._products

    @property
    def orders(self) -> 'Orders':
        """Acceso a operaciones del recurso Órdenes."""
        if not hasattr(self, '_orders'):
            from FalabellaAPIClient.orders import Orders
            self._orders = Orders(self)
        return self._orders

    @property
    def seller(self) -> 'Seller':
        """Acceso a operaciones del recurso Vendedor."""
        if not hasattr(self, '_seller'):
            from FalabellaAPIClient.seller import Seller
            self._seller = Seller(self)
        return self._seller

    @property
    def shipments(self) -> 'Shipments':
        """Acceso a operaciones del recurso Envíos."""
        if not hasattr(self, '_shipments'):
            from FalabellaAPIClient.shipments import Shipments
            self._shipments = Shipments(self)
        return self._shipments

    def signature(self, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Genera el diccionario de parámetros incluyendo la firma HMAC-SHA256 y timestamp ISO 8601.

        Args:
            parameters (dict, optional): Parámetros adicionales de la consulta.

        Returns:
            dict: Parámetros firmados y actualizados.
        """
        # Formato ISO 8601 relative to UTC sin microsegundos, e.g., 2026-06-25T14:26:07Z
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        if timestamp.endswith('+00:00'):
            timestamp = timestamp[:-6] + 'Z'

        params = {
            'UserID': self.user,
            'Version': '1.0',
            'Format': 'JSON',
            'Timestamp': timestamp
        }

        if parameters is not None:
            # Asegurar que no mutamos el dict original externamente
            params.update(parameters)

        api_key = self.key.encode('utf-8')
        sorted_params = sorted(params.items())
        concatenated = parse.urlencode(sorted_params).encode('utf-8')
        params['Signature'] = HMAC(api_key, concatenated, sha256).hexdigest()

        return params

    def query(self, method: str, params: Optional[Dict[str, Any]] = None,
              payload: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        """Realiza una petición HTTP a la API de Falabella y maneja errores.

        Args:
            method (str): Método HTTP (GET, POST, PUT, DELETE).
            params (dict, optional): Parámetros de la consulta (Action, etc.).
            payload (any, optional): Payload del request body (usualmente XML o JSON serializado).
            headers (dict, optional): Cabeceras adicionales para la petición.

        Returns:
            any: Respuesta JSON parseada o diccionario.

        Raises:
            FalabellaAPIError: Si la petición falla o la API retorna una respuesta de error.
        """
        if params is None:
            params = {}
        if headers is None:
            headers = {}

        merged_headers = dict(self.session.headers)
        merged_headers.update(headers)

        signed_params = self.signature(params)
        action = params.get("Action", "UnknownAction")

        try:
            response = self.session.request(
                method=method.upper(),
                url=self.url,
                params=signed_params,
                data=payload,
                headers=merged_headers
            )
        except Exception as e:
            logger.error(f"HTTP Request failed for action {action}: {e}")
            raise FalabellaAPIError(f"HTTP request failed: {e}")

        # Comprobar si el código de estado es de éxito
        if 200 <= response.status_code < 300:
            logger.info(f"{method.upper()} - {action} - Exitosa (Status: {response.status_code})")
            if not response.text.strip():
                return {}
            try:
                return response.json()
            except ValueError:
                return {"response_text": response.text}

        # Manejo de errores de la API
        error_msg = f"Error en la API (Status: {response.status_code})"
        try:
            res_json = response.json()
            if isinstance(res_json, dict):
                # La API de Seller Center puede devolver errores estructurados de varias formas
                if "ErrorResponse" in res_json:
                    head = res_json["ErrorResponse"].get("Head", {})
                    error_msg = head.get("ErrorMessage", error_msg)
                elif "SuccessResponse" in res_json:
                    # En algunos casos un status 4xx o 5xx puede tener un mensaje descriptivo
                    head = res_json["SuccessResponse"].get("Head", {})
                    if head.get("ErrorMessage"):
                        error_msg = head.get("ErrorMessage")
        except ValueError:
            if response.text:
                error_msg = response.text

        logger.warning(f"{method.upper()} - {action} - Fallida: {error_msg}")
        raise FalabellaAPIError(error_msg, status_code=response.status_code, response_body=response.text)
