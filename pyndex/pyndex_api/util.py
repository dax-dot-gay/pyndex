from typing import Any
from httpx import Client, BasicAuth, Response


class BaseInstance:
    def __init__(
        self,
        host: str,
        api_base: str = "/",
        username: str | None = None,
        password: str | None = None,
        api_token: str | None = None,
    ):
        """API instance object

        Args:
            host (str): Pyndex server URL
            api_base (str, optional): Base URL on server. Defaults to "/".
            username (str | None, optional): Username to login as. Defaults to None.
            password (str | None, optional): User password. Defaults to None.
            api_token (str | None, optional): API token (currently not implemented). Defaults to None.

        Raises:
            ValueError: Raised if arguments are provided incorrectly
        """
        if username and api_token:
            raise ValueError("Cannot set username & api token simultaneously")

        if username:
            self.username = username
            self.password = password

        else:
            self.username = "_token_"
            self.password = api_token

        self.host = host
        self.api_base = api_base
        self.client: Client | None = None
        self.devmode = False

    def url(self, *parts: str) -> str:
        """Generates a formatted URL from API parameters

        Args:
            *parts (str): Any number of path segments to add to the final URL

        Returns:
            str: Formatted URL
        """
        return "/".join(
            [
                i.strip("/")
                for i in [self.host, self.api_base, *parts]
                if len(i.strip("/")) > 0
            ]
        )

    def connect(self, client: Client | None = None):
        """Connect to API. If Client is passed, instead use that.

        Args:
            client (Client | None, optional): Pre-created HTTPX client, mostly for testing purposes.. Defaults to None.
        """
        self.client = (
            client
            if client
            else Client(
                auth=BasicAuth(username=self.username, password=self.password),
                follow_redirects=True,
            )
        )
        if client:
            self.devmode = True
        else:
            self.devmode = False

    def disconnect(self):
        """Disconnects from client"""
        if self.client and not self.client.is_closed:
            try:
                self.client.close()
            except:
                pass
            self.client = None


class ApiError(RuntimeError):
    def __init__(
        self, status_code: int, url: str, detail: str | None, *args: object
    ) -> None:
        """Extension of Exception initializer

        Args:
            status_code (int): HTTP status code
            url (str): Request URL
            detail (str | None): Error detail info
        """
        super().__init__(*args)
        self.status_code = status_code
        self.url = url
        self.detail = detail

    def __str__(self) -> str:
        """Formats the error with request info

        Returns:
            str: Formatted error
        """
        return f"Failed to call {self.url}: Error {self.status_code}{'\n\tReason: ' + self.detail if self.detail else ''}"

    @classmethod
    def from_response(cls, response: Response) -> "ApiError":
        """Constructs an APIError from an HTTPX response

        Args:
            response (Response): HTTPX response

        Returns:
            ApiError: Constructed APIError
        """
        try:
            detail = response.json()["detail"]
        except:
            detail = None
        return cls(response.status_code, response.url, detail)
