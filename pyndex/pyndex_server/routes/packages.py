from litestar import Controller, post, get, Request
import os
from typing import Annotated, Optional
from httpx import AsyncClient
from ..models import (
    FileMetadata,
    Package,
    PackageList,
    PackageListItem,
    PackageDetail,
    APIMeta,
)
from ..context import Context
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.exceptions import *


class PackageController(Controller):
    """
    Performs package-related tasks
    """
    path = "/packages"

    @post("/upload")
    async def upload_file(
        self,
        context: Context,
        data: Annotated[FileMetadata, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> FileMetadata:
        """Uploads a file to the index

        Args:
            context (Context): Application context
            data (Annotated[FileMetadata, Body, optional): Multipart form data containing file metadata & the file blob itself. Metadata format from `https://warehouse.pypa.io/api-reference/legacy.html#upload-api`

        Raises:
            MethodNotAllowedException: Raised if the file already exists

        Returns:
            FileMetadata: Metadata about the uploaded file
        """
        try:
            await data.save(str(context.root.joinpath("index")))
        except FileExistsError:
            raise MethodNotAllowedException(
                detail="Cannot overwrite an existing version of a package."
            )

        return data

    @get(
        "/{project_name:str}",
        response_headers={"Content-Type": "application/vnd.pypi.simple.v1+json"},
    )
    async def get_file_info(
        self, context: Context, project_name: str, request: Request, local: bool = False
    ) -> PackageDetail:
        """Retrieves a list of files associated with the given project (across all versions)

        Args:
            context (Context): Application context
            project_name (str): Project name
            request (Request): Litestar Request object
            local (bool, optional): Whether to only query local (non-proxied) packages. Defaults to False.

        Raises:
            NotFoundException: Raised if the package couldn't be found

        Returns:
            PackageDetail: Details about the package. Format based on `https://packaging.python.org/en/latest/specifications/simple-repository-api/#project-detail`
        """
        if not os.path.exists(context.root.joinpath("index", project_name)):
            if len(context.config.proxies) > 0 and not local:
                for proxy in context.config.proxies:
                    async with AsyncClient(follow_redirects=True) as client:
                        result = await client.get(
                            proxy.urls.index.format(project_name=project_name),
                            headers={"Accept": "application/vnd.pypi.simple.v1+json"},
                        )
                        if result.is_success:
                            return PackageDetail(**result.json())

            raise NotFoundException(f"Unknown project {project_name}.")

        base_url = str(request.base_url).rstrip("/")
        package = Package.assemble_package(
            context.root.joinpath("index", project_name), url_base=base_url
        )
        return package.detail(url_base=base_url)

    @get("/", response_headers={"Content-Type": "application/vnd.pypi.simple.v1+json"})
    async def get_file_list(self, context: Context) -> PackageList:
        """Returns a list of all packages on the local index. Does not include proxied packages to avoid duplication & confusion

        Args:
            context (Context): Application context

        Returns:
            PackageList: PackageList object. Based on `https://packaging.python.org/en/latest/specifications/simple-repository-api/#project-list`
        """
        names = os.listdir(context.root.joinpath("index"))
        return PackageList(
            meta=APIMeta(), projects=[PackageListItem(name=name) for name in names]
        )

    @get("/detail/{project_name:str}")
    async def get_package_detail(
        self,
        context: Context,
        project_name: str,
        request: Request,
        local: Optional[bool] = False,
    ) -> Package:
        """Gets in-depth information about a specific package's latest version

        Args:
            context (Context): Application context
            project_name (str): Project name
            request (Request): Litestar Request object
            local (Optional[bool], optional): Whether to only query the local index. Defaults to False.

        Raises:
            NotFoundException: If package wasn't found

        Returns:
            Package: Package details. Based on `https://warehouse.pypa.io/api-reference/json.html#project`
        """
        try:
            return Package.assemble_package(
                context.root.joinpath("index", project_name), url_base=request.base_url
            )
        except FileNotFoundError:
            if len(context.config.proxies) > 0 and not local:
                for proxy in context.config.proxies:
                    if proxy.urls.package:
                        async with AsyncClient(follow_redirects=True) as client:
                            result = await client.get(
                                proxy.urls.package.format(project_name=project_name)
                            )
                            if result.is_success:
                                return Package(**result.json(), local=False)
            raise NotFoundException("Unknown package.")

    @get("/detail/{project_name:str}/{version:str}")
    async def get_package_version_detail(
        self,
        context: Context,
        project_name: str,
        version: str,
        request: Request,
        local: Optional[bool] = False,
    ) -> Package:
        """Gets in-depth information about a specific package's specified version

        Args:
            context (Context): Application context
            project_name (str): Project name
            version (str): Project version
            request (Request): Litestar Request object
            local (Optional[bool], optional): Whether to only query the local index. Defaults to False.

        Raises:
            NotFoundException: If package wasn't found

        Returns:
            Package: Package details. Based on `https://warehouse.pypa.io/api-reference/json.html#release`
        """
        try:
            return Package.assemble_package(
                context.root.joinpath("index", project_name),
                version=version,
                url_base=request.base_url,
            )
        except FileNotFoundError:
            if len(context.config.proxies) > 0 and not local:
                for proxy in context.config.proxies:
                    if proxy.urls.package:
                        async with AsyncClient(follow_redirects=True) as client:
                            result = await client.get(
                                proxy.urls.package.format(
                                    project_name=project_name + "/" + version
                                )
                            )
                            if result.is_success:
                                return Package(**result.json(), local=False)
            raise NotFoundException("Unknown package.")
        except KeyError:
            raise NotFoundException(f"Unknown version {version}")
