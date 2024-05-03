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

    def url(self, *parts: str) -> str:
        return "/".join(
            [
                i.strip("/")
                for i in [self.host, self.api_base, *parts]
                if len(i.strip("/")) > 0
            ]
        )

    def connect(self, client: Client | None = None):
        self.client = (
            client
            if client
            else Client(
                auth=BasicAuth(username=self.username, password=self.password),
                follow_redirects=True,
            )
        )

    def disconnect(self):
        if self.client and not self.client.is_closed:
            self.client.close()
            self.client = None


class ApiError(RuntimeError):
    def __init__(
        self, status_code: int, url: str, detail: str | None, *args: object
    ) -> None:
        super().__init__(*args)
        self.status_code = status_code
        self.url = url
        self.detail = detail

    def __str__(self) -> str:
        return f"Failed to call {self.url}: Error {self.status_code}{'\n\tReason: ' + self.detail if self.detail else ''}"

    @classmethod
    def from_response(cls, response: Response) -> "ApiError":
        try:
            detail = response.json()["detail"]
        except:
            detail = None
        return cls(response.status_code, response.url, detail)
