class Products:

    def __init__(self, service, session) -> None:
        """_summary_

        Args:
            service (_type_): _description_
            session (_type_): _description_
        """
        self.service = service
        self.session = session

    def get(self, limit: int = 1000, **kwargs: dict) -> dict:
        """get information for one product or a product list

        Args:
            limit (int, optional): output results 1 to 1000.
            Defaults to 1000.

        Returns:
            dict: product information
        """
        params = {
            "Action": "GetProducts",
            "Limit": limit
        }

        if kwargs:
            params.update(kwargs)

        return self.service.request(self.session, 'get', params)

    def create(self, payload: dict) -> dict:
        """create a products

        Args:
            payload (_type_): product information

        Returns:
            dict: operation response
        """
        params = {
            "Action": "ProductCreate"
        }

        return self.service.request(self.session, 'post', params, payload)

    def update(self, payload: dict) -> dict:
        """update products

        Args:
            payload (XML): product information

        Returns:
            dict: operation response
        """
        params = {
            "Action": "ProductUpdate"
        }

        return self.service.request(self.session, 'post', params, payload)

    def remove(self, payload) -> dict:
        """remove product

        Args:
            payload (_type_): _description_

        Returns:
            dict: operation response
        """
        params = {
            "Action": "ProductRemove"
        }

        return self.service.request(self.session, 'post', params, payload)

    def brands(self) -> dict:
        """search seller brands

        Returns:
            dict: seller brands
        """
        params = {
            "Action": "GetBrands"
        }

        return self.service.request(self.session, 'get', params)
