from typing import Annotated
from litestar import Controller, post
from ..models import FileMetadata
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
    ) -> FileMetadata:
        try:
            await data.save(str(context.root.joinpath("index")))
        except FileExistsError:
            raise MethodNotAllowedException(
                detail="Cannot overwrite an existing version of a package."
            )

        return data
