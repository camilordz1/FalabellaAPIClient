from typing import Any, Dict
from FalabellaAPIClient.actions import Actions


class Seller(Actions):
    """Operaciones relacionadas con el perfil del Vendedor en la API de Falabella/Linio."""

    def __init__(self, service_or_client: Any = None, session: Any = None) -> None:
        """Inicializa el recurso del Vendedor.

        Args:
            service_or_client (Any, optional): Instancia de FalabellaClient (nueva arquitectura)
                o Service (arquitectura heredada).
            session (Any, optional): Instancia de Session (solo para arquitectura heredada).
        """
        if session is not None:
            self.service = service_or_client
            self.session = session
            self._legacy = True
            super().__init__(None)
        else:
            super().__init__(service_or_client)
            self._legacy = False

    def get(self) -> Dict[str, Any]:
        """Obtiene la información y estado de la cuenta del vendedor.

        Returns:
            dict: Datos del perfil del vendedor.
        """
        params = {
            "Action": "GetSeller"
        }

        if getattr(self, '_legacy', False):
            return self.service.request(self.session, 'get', params)
        return self.client.query('get', params=params)
