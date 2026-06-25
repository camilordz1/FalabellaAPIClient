from hmac import HMAC
from urllib import parse
from hashlib import sha256
from datetime import datetime
import warnings


class Session:
    """Clase heredada (Legacy) para manejar la sesión y credenciales.

    Se recomienda migrar al uso de FalabellaClient.
    """

    headers = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }

    def __init__(self, user: str, key: str, service: str = "linio",
                 country: str = "co") -> None:
        """Inicializa la sesión heredada."""
        warnings.warn(
            "La clase 'Session' es obsoleta. Use 'FalabellaClient' en su lugar.",
            DeprecationWarning,
            stacklevel=2
        )
        self.user = user
        self.key = key
        self.service = service
        self.country = country

        self.url = f"https://sellercenter-api.linio.com.{country}"
        if service == "falabella":
            self.url = "https://sellercenter-api.falabella.com"

    def signature(self, parameters: dict = None) -> dict:
        """Genera la firma de manera heredada."""
        params = {
            'UserID': self.user,
            'Version': '1.0',
            'Format': 'JSON',
            'Timestamp': datetime.now().isoformat()
        }

        if parameters is not None:
            params.update(parameters)

        api_key = self.key.encode('utf-8')
        sorted_params = sorted(params.items())
        concatenated = parse.urlencode(sorted_params).encode('utf-8')
        params['Signature'] = HMAC(api_key, concatenated, sha256).hexdigest()

        return params
