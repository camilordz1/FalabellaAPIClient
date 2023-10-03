from hmac import HMAC
from urllib import parse
from hashlib import sha256
from datetime import datetime


class Session:

    headers = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }

    def __init__(self, user: str, key: str, service: str = "linio",
                 country: str = "co") -> None:
        """create a session to use falabella's API

        Args:
            user (str): email
            key (str): api key
            service (str, optional): select falabella or linio.
            Defaults to "linio".
            country (str, optional): country. Defaults to "co".
        """

        self.user = user
        self.key = key

        self.url = f"https://sellercenter-api.linio.com.{country}"
        if service == "falabella":
            self.url = "https://sellercenter-api.falabella.com"

    def signature(self, parameters: dict = None) -> dict:
        """generate signature.

        Args:
            parameters (dict, optional): Additional parameters.
            Defaults to None.

        Returns:
            dict: parameters
        """

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
