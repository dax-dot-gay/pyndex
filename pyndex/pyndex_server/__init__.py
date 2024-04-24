from typing import Annotated, Any
from litestar import Litestar, post
from litestar.params import Body
from litestar.enums import RequestEncodingType


@post("/")
async def test_upload(
    data: Annotated[Any, Body(media_type=RequestEncodingType.MULTI_PART)]
) -> Any:
    print(await data["content"].read())
    return None


app = Litestar(route_handlers=[test_upload])
