from requests import request as rq


class Service:

    def request(self, session: object, method: str, params: dict = {},
                payload: dict = {}, headers: dict = {}) -> dict | None:
        """request method

        Args:
            session (object): credentials object
            method (str): select https method
            url (str): url endpoint
            params (dict, optional): parameters. Defaults to {}.
            payload (dict, optional): data. Defaults to {}.
            headers (dict, optional): headers. Defaults to {}.

        Returns:
            dict | None: server response
        """

        response = rq(method,
                      session.url,
                      data=payload,
                      params=session.signature(params),
                      headers=headers)

        if response.status_code == 200:

            return response.json()

        return None
