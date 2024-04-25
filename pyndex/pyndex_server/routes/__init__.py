from typing import Annotated, Any
from litestar import Router, post
from litestar.enums import RequestEncodingType
from litestar.params import Body
from .pypi import PypiController
from .files import FilesController
from .packages import PackagesController


def make_api_router(base: str) -> Router:
    return Router(
        base, route_handlers=[PypiController, FilesController, PackagesController]
    )
