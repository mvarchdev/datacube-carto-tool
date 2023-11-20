# first line: 32
    def _make_request_wrapped(self, endpoint, params=None):
        """
                Makes a cached HTTP GET request to a specified endpoint.
                :param endpoint: The API endpoint to query.
                :param params: Optional parameters for the request.
                :return: The response object or None in case of an error.
                """
        try:
            response = self.session.get(f"{self.BASE_URL}{endpoint}", params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as err:
            logging.error(f"Request error: {err}")
            return None
