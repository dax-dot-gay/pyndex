from typing import Callable
from httpx import Client
from .models import *
from .wrappers import upload, ProgressUpdate


class Pyndex:
    """API connection instance for the Pyndex API"""

    def __init__(
        self,
        api_url: str,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
    ) -> None:
        """Pyndex connection initializer

        Args:
            api_url (str): Base API path
            username (str | None, optional): Username, if required. Defaults to None.
            password (str | None, optional): Password, if required. Defaults to None.
            token (str | None, optional): API token, if required. Defaults to None.
        """
        self.url_base = api_url.rstrip("/")

        if username:
            self.username = username
            self.password = password if password else ""
        elif token:
            self.username = "_token_"
            self.password = token
        else:
            self.username = ""
            self.password = ""

        self.client = None

    def __enter__(self) -> "Pyndex":
        self.client = Client()
        return self

    def __exit__(self, *args, **kwargs):
        if self.client:
            self.client.close()

    def url(self, endpoint: str) -> str:
        """Generates a formatted URL from the base URL and an endpoint

        Args:
            endpoint (str): API endpoint

        Returns:
            str: Formatted URL
        """
        return self.url_base + "/" + endpoint.lstrip("/")

    def get_package(
        self, name: str, version: str | None = None, allow_proxy: bool = True
    ) -> Package | None:
        """Gets information about a package, if it exists.

        Args:
            name (str): Package name
            version (str | None, optional): Optional package version to get. Defaults to None.
            allow_proxy (bool, optional): Whether to return results from remote proxies as well. Defaults to True.

        Returns:
            Package | None: Package object if found, otherwise None
        """
        result = self.client.get(
            self.url(f"/packages/{name}{'/' + version if version else ''}"),
            params={"local": not allow_proxy},
        )
        if result.is_success:
            return Package(**result.json())
        return None

    def get_package_names(self) -> list[str]:
        """Gets a list of all package names on the local index. Does not index remote proxies to avoid performance issues.

        Returns:
            list[str]: List of package names available
        """
        result = self.client.get(
            self.url("/pypi"),
        )
        if result.is_success:
            return [i["name"] for i in result.json()["projects"]]
        return []

    def get_package_files(
        self, name: str, allow_proxy: bool = True
    ) -> list[PackageFileDetail]:
        """Gets a list of all files associated with a package

        Args:
            name (str): Package name
            allow_proxy (bool, optional): Whether to return results from remote proxies as well. Defaults to True.

        Returns:
            list[PackageFileDetail]: List of FileDetail objects
        """
        result = self.client.get(
            self.url(f"/pypi/{name}"), params={"local": not allow_proxy}
        )
        if result.is_success:
            return [PackageFileDetail(**i) for i in result.json()["files"]]
        return []

    def upload(
        self, *dists: str, progress: Callable[[ProgressUpdate], None] | None = None
    ) -> None:
        """Uploads any number of dist folders to the target Pyndex

        Args:
            *dists (str): Any number of distribution paths to upload
            progress (Callable[[ProgressUpdate], None] | None, optional): Progress callback function. Defaults to None.
        """
        upload(
            *dists,
            progress_callback=progress,
            repository_url=self.url("/pypi/upload"),
            username=self.username,
            password=self.password,
        )
