import json
import os
from litestar import Controller, get, Response
from ..context import Context
from litestar.response import File
from litestar.exceptions import *
from ..models import FileMetadata


class FilesController(Controller):
    path = "/files"

    @get("{project_name:str}/{project_version:str}/{filename:str}")
    async def get_project_file(
        self, context: Context, project_name: str, project_version: str, filename: str
    ) -> File:

        if filename.endswith(".metadata"):
            if not context.root.joinpath(
                "index",
                project_name,
                project_version,
                filename.rsplit(".", maxsplit=1)[0] + ".json",
            ).exists():
                raise NotFoundException("Requested file does not exist.")
            with open(
                context.root.joinpath(
                    "index",
                    project_name,
                    project_version,
                    filename.rsplit(".", maxsplit=1)[0] + ".json",
                ),
                "r",
            ) as metafile:
                meta = FileMetadata(**json.load(metafile))

            return Response(
                meta.as_metadata(), status_code=200, media_type="text/plain"
            )
        else:
            if not context.root.joinpath(
                "index", project_name, project_version, filename
            ).exists():
                raise NotFoundException("Requested file does not exist.")
            return File(
                context.root.joinpath("index", project_name, project_version, filename),
                filename=filename,
            )
