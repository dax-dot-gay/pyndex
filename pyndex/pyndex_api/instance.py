from twine.commands.upload import upload as twine_upload
from twine.settings import Settings


class PynDex:
    def __init__(
        self,
        url: str,
        username: str = None,
        password: str = None,
        api_token: str = None,
    ):
        """Initialize the PynDex wrapper

        Args:
            url (str): Base API url (ie https://pyndex.example.com/api)
            username (str, optional): Username to authenticate with. Defaults to None.
            password (str, optional): Password to authenticate with. Defaults to None.
            api_token (str, optional): API token to authenticate with (cannot be specified with username). Defaults to None.
        """
        if username and api_token:
            raise ValueError(
                "Cannot specify username/password & api_token simultaneously"
            )

        if username:
            self.username = username
            self.password = password if password else ""
        elif api_token:
            self.username = "__token__"
            self.password = api_token
        else:
            self.username = ""
            self.password = ""

        self.url = url.rstrip("/")

    def upload_package(self, *dists: str, comment: str | None = None) -> None:
        """Wrap the Twine upload process

        Args:
            *dists (str): Any number of distribution files/globs to upload
            comment (str | None, optional): An optional comment to add to the upload. Defaults to None.
        """
        twine_upload(
            Settings(
                username=self.username,
                password=self.password,
                non_interactive=True,
                comment=comment,
                repository_url=f"{self.url}/pypi/upload",
                disable_progress_bar=True,
            ),
            list(dists),
        )
