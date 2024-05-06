from typing import Any, Callable

from pydantic import BaseModel
from .base import BaseOperator, BaseOperatorModel
from ...common import Package, upload, ProgressUpdate, PackageFileDetail
from ..util import ApiError


class PackageItem(Package, BaseOperatorModel["PackageOperator"]):

    def __init__(self, operator: "PackageOperator" = None, **data):
        super().__init__(**data)
        self._operator = operator

    def get_version(self, version: str) -> "PackageItem | None":
        """Gets a different version of this package

        Args:
            version (str): Version to get

        Returns:
            PackageItem | None: PackageItem if found, None otherwise
        """
        return self.operator(self.info.name, version=version, local=self.local)

    def get_files(self) -> list[PackageFileDetail]:
        """Returns all files associated with this package

        Raises:
            ApiError.from_response: If the API returns an error response

        Returns:
            list[PackageFileDetail]: List of package files
        """
        result = self.client.get(
            self.url("packages", self.info.name), params={"local": self.local}
        )
        if result.is_success:
            return [PackageFileDetail(**i) for i in result.json()["files"]]
        raise ApiError.from_response(result)


class LazyPackageList:
    def __init__(self, names: list[str], operator: "PackageOperator") -> None:
        self.names = names
        self.operator = operator
        self.index = -1

    def __iter__(self):
        return self

    def __next__(self) -> PackageItem:
        self.index += 1
        if self.index < len(self.names):
            return self.operator(self.names[self.index], local=True)
        raise StopIteration


class PackageOperator(BaseOperator):
    def __call__(
        self, name: str, version: str | None = None, local: bool = False
    ) -> PackageItem | None:
        """Provides a call signature for this operator that provides a single PackageItem based on name & optional version

        Args:
            name (str): Package name
            version (str | None, optional): Optional version. Defaults to None.
            local (bool, optional): Whether to only return local packages. Defaults to None.

        Returns:
            PackageItem | None: Package found, or None otherwise
        """
        if version:
            result = self.client.get(
                self.url("packages", "detail", name, version), params={"local": local}
            )
        else:
            result = self.client.get(
                self.url("packages", "detail", name), params={"local": local}
            )

        if result.is_success:
            return PackageItem(operator=self, **result.json())
        return None

    def upload(
        self, *dists: str, on_progress: Callable[[ProgressUpdate], None] | None = None
    ) -> list[PackageItem]:
        """Wrapper around twine upload that uploads any number of dist/ directories to the index.

        Args:
            *dists (str): Any number of dist/ directories to upload from
            on_progress (Callable[[ProgressUpdate], None] | None, optional): An optional callback to call with progress updates. Defaults to None.

        Returns:
            list[PackageItem]: List of uploaded packages
        """
        packages = upload(
            *dists,
            progress_callback=on_progress,
            repository_url=self.url("packages", "upload"),
            username=self.instance.username,
            password=self.instance.password,
            client=self.client if self.instance.devmode else None,
        )

        return [self(name, version=version, local=True) for name, version in packages]

    def all(self) -> LazyPackageList:
        """Returns an iterator over all local packages

        Raises:
            ApiError.from_response: If an error occurs in calling /packages

        Returns:
            LazyPackageList: Iterator over all packages
        """
        result = self.client.get(self.url("packages"))
        if result.is_success:
            names = [i["name"] for i in result.json()["projects"]]
            return LazyPackageList(names, self)
        raise ApiError.from_response(result)
