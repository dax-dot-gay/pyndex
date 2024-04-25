import os
from typing import Annotated
from httpx import AsyncClient
from litestar import Controller, post, get, Request
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


class PypiController(Controller):
    path = "/pypi"

    @post("/upload")
    async def upload_file(
        self,
        context: Context,
        data: Annotated[FileMetadata, Body(media_type=RequestEncodingType.MULTI_PART)],
        request: Request,
    ) -> FileMetadata:
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
        self, context: Context, project_name: str, request: Request
    ) -> PackageDetail:
        if not os.path.exists(context.root.joinpath("index", project_name)):
            if len(context.config.proxies) > 0:
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
        names = os.listdir(context.root.joinpath("index"))
        return PackageList(
            meta=APIMeta(), projects=[PackageListItem(name=name) for name in names]
        )
