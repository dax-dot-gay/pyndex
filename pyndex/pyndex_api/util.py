from httpx import Client, BasicAuth


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
                for i in list(self.host, self.api_base, *parts)
                if len(i.strip("/") > 0)
            ]
        )

    def connect(self):
        self.client = Client(
            auth=BasicAuth(username=self.username, password=self.password),
            follow_redirects=True,
        )

    def disconnect(self):
        if self.client and not self.client.is_closed:
            self.client.close()
            self.client = None
