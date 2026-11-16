import logging
import platform
import time
import warnings
import requests
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime, timezone
from hmac import HMAC
from urllib import parse
from hashlib import sha256

logger = logging.getLogger("falabella")


class FalabellaAPIError(Exception):
    """Excepción lanzada ante errores en las respuestas de la API de Falabella."""
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_body: Optional[str] = None, *, error_code: Optional[str] = None,
                 error_type: Optional[str] = None, action: Optional[str] = None,
                 details: Optional[List[Dict[str, Any]]] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.error_code = error_code
        self.error_type = error_type
        self.action = action
        self.details = details if details is not None else []


def _parse_error_response(body: Any) -> Optional[Dict[str, Any]]:
    """Extract error data from an ``ErrorResponse`` envelope.

    Args:
        body: Parsed JSON body returned by the API.

    Returns:
        dict: ``message``, ``code``, ``type`` and ``details`` (always a list), or
        ``None`` when the body is not a dict containing an ``ErrorResponse``.
    """
    if not isinstance(body, dict) or "ErrorResponse" not in body:
        return None

    error = body["ErrorResponse"]
    if not isinstance(error, dict):
        return None

    head = error.get("Head")
    if not isinstance(head, dict):
        head = {}

    error_body = error.get("Body")
    if not isinstance(error_body, dict):
        error_body = {}

    details = error_body.get("ErrorDetail")
    if isinstance(details, dict):
        details = [details]
    elif not isinstance(details, list):
        details = []

    return {
        "message": head.get("ErrorMessage"),
        "code": head.get("ErrorCode"),
        "type": head.get("ErrorType"),
        "details": details,
    }


class FalabellaClient:
    """Cliente unificado para interactuar con la API de Falabella y Linio Seller Center."""

    BUSINESS_UNITS = {"FACL", "FACO", "FAPE"}

    @staticmethod
    def _is_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @classmethod
    def _valid_timeout(cls, value: Any) -> bool:
        if cls._is_number(value):
            return value > 0
        if isinstance(value, tuple) and len(value) == 2:
            return all(cls._is_number(part) and part > 0 for part in value)
        return False

    @staticmethod
    def _normalize_component(name: str, value: Any, allow_int: bool = False) -> str:
        if allow_int and isinstance(value, int) and not isinstance(value, bool):
            value = str(value)
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a string")
        value = value.strip()
        if not value or "/" in value or any(ord(char) < 32 for char in value):
            raise ValueError(
                f"{name} must be non-empty and contain no '/' or control characters"
            )
        return value

    def __init__(self, user: str, key: str, service: str = "falabella", country: str = "co",
                 *, timeout: Union[float, Tuple[float, float]] = 30.0, max_retries: int = 3,
                 backoff_factor: float = 1.0, seller_id: Optional[str] = None,
                 business_unit: str = "FACO", integration_type: str = "PROPIA") -> None:
        """Inicializa el cliente de Falabella.

        Args:
            user (str): Correo electrónico del usuario (UserID).
            key (str): Llave API (API Key).
            service (str, optional): Servicio a usar ('falabella' o 'linio'). Por defecto es 'falabella'.
            country (str, optional): Código del país. Por defecto es 'co'.
            timeout (float, optional): Timeout de cada petición HTTP en segundos. Por defecto es 30.0.
            max_retries (int, optional): Reintentos máximos de peticiones transitorias. Por defecto es 3.
            backoff_factor (float, optional): Base del backoff exponencial. Por defecto es 1.0.
            seller_id (str, optional): Seller id usado en el User-Agent requerido por Falabella.
            business_unit (str, optional): Unidad de negocio ('FACL', 'FACO' o 'FAPE'). Por defecto 'FACO'.
            integration_type (str, optional): Tipo de integración del User-Agent. Por defecto 'PROPIA'.
        """
        if not self._valid_timeout(timeout):
            raise ValueError(
                "timeout must be a positive number or a (connect, read) tuple of positive numbers"
            )
        if (not isinstance(max_retries, int) or isinstance(max_retries, bool)
                or max_retries < 0):
            raise ValueError("max_retries must be an integer greater than or equal to 0")
        if not self._is_number(backoff_factor) or backoff_factor < 0:
            raise ValueError("backoff_factor must be a number greater than or equal to 0")

        normalized_unit = business_unit.upper() if isinstance(business_unit, str) else ""
        if normalized_unit not in self.BUSINESS_UNITS:
            raise ValueError(f"business_unit must be one of {sorted(self.BUSINESS_UNITS)}")
        if seller_id is not None:
            seller_id = self._normalize_component("seller_id", seller_id, allow_int=True)
        integration_type = self._normalize_component("integration_type", integration_type)

        self.user = user
        self.key = key
        self.service = service.lower()
        self.country = country.lower()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.seller_id = seller_id
        self.business_unit = normalized_unit
        self.integration_type = integration_type
        self._sleep = time.sleep

        # Configurar URL base
        if self.service == "falabella":
            self.url = "https://sellercenter-api.falabella.com"
        else:
            self.url = f"https://sellercenter-api.linio.com.{self.country}"

        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json'
        })
        if seller_id is not None:
            self.session.headers["User-Agent"] = (
                f"{seller_id}/Python/{platform.python_version()}/"
                f"{integration_type}/{normalized_unit}"
            )
        else:
            warnings.warn(
                "The User-Agent required by Falabella is missing: pass seller_id. "
                "It will be mandatory in the next major version.",
                UserWarning,
                stacklevel=2,
            )

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

    def _prepare_request(self, payload: Optional[Any],
                         headers: Dict[str, str]) -> Tuple[Optional[Any], Dict[str, str]]:
        """Build body and headers, encoding str/bytes payloads as UTF-8 XML."""
        merged_headers = dict(self.session.headers)
        merged_headers.update(headers)

        if payload is None:
            return None, merged_headers
        if isinstance(payload, str):
            body = payload.encode("utf-8")
        elif isinstance(payload, bytes):
            body = payload
        else:
            raise TypeError("payload must be None, str or bytes")

        if not any(name.lower() == "content-type" for name in merged_headers):
            merged_headers["Content-Type"] = "application/xml; charset=utf-8"
        return body, merged_headers

    @staticmethod
    def _retry_after_seconds(response: requests.Response) -> Optional[float]:
        value = response.headers.get("Retry-After")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _retry_delay(self, attempt: int, retry_after: Optional[float]) -> float:
        delay = retry_after if retry_after is not None else self.backoff_factor * (2 ** (attempt - 1))
        return max(0.0, min(delay, 60.0))

    @staticmethod
    def _is_retryable(method: str, status_code: int, error_code: Optional[str]) -> bool:
        if status_code == 429 or (error_code is not None and str(error_code) == "429"):
            return True
        return status_code >= 500 and method == "GET"

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

        http_method = method.upper()
        action = params.get("Action", "UnknownAction")
        body, merged_headers = self._prepare_request(payload, headers)

        attempt = 0
        while True:
            attempt += 1
            # The timestamp is part of the signature, so re-sign every attempt.
            signed_params = self.signature(params)

            try:
                response = self.session.request(
                    method=http_method,
                    url=self.url,
                    params=signed_params,
                    data=body,
                    headers=merged_headers,
                    timeout=self.timeout,
                )
            except requests.RequestException as e:
                if (http_method == "GET"
                        and isinstance(e, (requests.ConnectionError, requests.Timeout))
                        and not isinstance(e, (requests.exceptions.SSLError,
                                               requests.exceptions.ProxyError))
                        and attempt <= self.max_retries):
                    delay = self._retry_delay(attempt, None)
                    logger.warning(
                        f"{http_method} - {action} - Retry {attempt}/{self.max_retries} "
                        f"in {delay}s: {e}"
                    )
                    self._sleep(delay)
                    continue
                logger.error(f"HTTP Request failed for action {action}: {e}")
                raise FalabellaAPIError(f"HTTP request failed: {e}") from e

            retry_after = self._retry_after_seconds(response)
            error = None

            if 200 <= response.status_code < 300:
                logger.info(
                    f"{http_method} - {action} - Exitosa (Status: {response.status_code})"
                )
                if not response.text.strip():
                    return {}
                try:
                    parsed = response.json()
                except ValueError:
                    return {"response_text": response.text}

                error = _parse_error_response(parsed)
                if error is None:
                    return parsed

                error_msg = error["message"] or (
                    f"Error en la API (Status: {response.status_code})"
                )
                error_code = error["code"]
            else:
                error_msg = f"Error en la API (Status: {response.status_code})"
                error_code = None
                try:
                    res_json = response.json()
                except ValueError:
                    if response.text:
                        error_msg = response.text
                else:
                    error = _parse_error_response(res_json)
                    if error is not None:
                        error_msg = error["message"] or error_msg
                        error_code = error["code"]
                    elif isinstance(res_json, dict) and "SuccessResponse" in res_json:
                        # Some 4xx/5xx responses carry a descriptive message here.
                        head = res_json["SuccessResponse"].get("Head", {})
                        if head.get("ErrorMessage"):
                            error_msg = head.get("ErrorMessage")

            if (self._is_retryable(http_method, response.status_code, error_code)
                    and attempt <= self.max_retries):
                delay = self._retry_delay(attempt, retry_after)
                logger.warning(
                    f"{http_method} - {action} - Retry {attempt}/{self.max_retries} "
                    f"in {delay}s: {error_msg}"
                )
                self._sleep(delay)
                continue

            logger.warning(f"{http_method} - {action} - Fallida: {error_msg}")
            raise FalabellaAPIError(
                error_msg,
                status_code=response.status_code,
                response_body=response.text,
                error_code=error_code,
                error_type=error["type"] if error else None,
                action=action,
                details=error["details"] if error else [],
            )
