from typing import Annotated, Any
from litestar import Router, post
from litestar.enums import RequestEncodingType
from litestar.params import Body


@post("/")
async def upload(
    data: Annotated[Any, Body(media_type=RequestEncodingType.MULTI_PART)]
) -> None:
    print(data)
    return None


def make_api_router(base: str) -> Router:
    return Router(base, route_handlers=[upload])
