from functools import cached_property
from typing import Callable
from unittest import result
from httpx import Client, Response
import httpx
from .models import *
from .wrappers import upload, ProgressUpdate


class ApiError(RuntimeError):
    def __init__(self, *args: object, response: Response | None = None) -> None:
        super().__init__(*args)
        self.response = response
        self.content = self.response.json() if self.response else {}

    @property
    def code(self) -> int:
        return self.response.status_code if self.response else 0

    @property
    def reason(self) -> str | None:
        return self.content.get("detail")


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
        self.client = Client(auth=httpx.BasicAuth(self.username, self.password))
        return self

    def __exit__(self, *args, **kwargs):
        if self.client:
            self.client.close()

    @cached_property
    def user(self) -> RedactedAuth | None:
        result = self.client.get(self.url("/meta/users/me"))
        if result.is_success:
            return RedactedAuth(**result.json())
        return None

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

    @cached_property
    def admin(self) -> bool:
        result = self.client.get(self.url("/meta/users/me/admin"))
        if result.is_success:
            return result.json()
        return False

    def create_user(self, username: str, password: str | None = None) -> RedactedAuth:
        result = self.client.post(
            self.url("/meta/admin/user"),
            json={"username": username, "password": password},
        )
        if result.is_success:
            return RedactedAuth(**result.json())
        else:
            raise ApiError(response=result)

    def get_users(self) -> list[RedactedAuth]:
        result = self.client.get(self.url("/meta/users"))
        if result.is_success:
            return [RedactedAuth(**i) for i in result.json()]
        else:
            raise ApiError(response=result)

    def create_group(self, name: str, display_name: str | None = None) -> AuthGroup:
        result = self.client.post(
            self.url("/meta/admin/group"),
            json={"name": name, "display_name": display_name},
        )
        if result.is_success:
            return AuthGroup(**result.json())
        else:
            raise ApiError(response=result)

    def get_user(
        self, username: str | None = None, user_id: str | None = None
    ) -> RedactedAuth | None:
        if (username == None and user_id == None) or (
            username != None and user_id != None
        ):
            raise ValueError("Must specify username OR user_id")

        if username:
            result = self.client.get(self.url(f"/meta/users/name/{username}"))
        else:
            result = self.client.get(self.url(f"/meta/users/id/{user_id}"))
        if result.is_success:
            print(result.json())
            return RedactedAuth(**result.json())
        return None

    def add_user_to_groups(self, username: str, groups: list[str]) -> RedactedAuth:
        user = self.get_user(username=username)
        if not user:
            raise ValueError("Unknown username")

        result = self.client.post(
            self.url(f"/meta/admin/user/{user.id}/groups"), json=groups
        )
        if result.is_success:
            return RedactedAuth(**result.json())
        else:
            raise ApiError(response=result)
