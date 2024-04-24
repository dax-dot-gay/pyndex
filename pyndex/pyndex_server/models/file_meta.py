import json
import os
import pathlib
from typing import Optional
from pydantic import BaseModel, Field, computed_field
from litestar.datastructures import UploadFile


class FileMetadata(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    metadata_version: str
    name: str
    version: str
    platform: Optional[list[str]] = None
    supported_platform: Optional[list[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    description_content_type: Optional[str] = None
    keywords: Optional[str] = None
    home_page: Optional[str] = None
    download_url: Optional[str] = None
    author: Optional[str] = None
    author_email: Optional[str] = None
    maintainer: Optional[str] = None
    maintainer_email: Optional[str] = None
    license: Optional[str] = None
    classifiers: Optional[list[str]] = None
    requires_dist: Optional[list[str]] = None
    requires_python: Optional[str] = None
    requires_external: Optional[list[str]] = None
    project_urls: Optional[list[str]] = None
    provides_dist: Optional[list[str]] = None
    obsoletes_dist: Optional[list[str]] = None
    provides: Optional[list[str]] = None
    requires: Optional[list[str]] = None
    obsoletes: Optional[list[str]] = None
    comment: Optional[str] = None
    action: str = Field(validation_alias=":action")
    protocol_version: int
    filetype: Optional[str] = None
    md5_digest: Optional[str] = None
    sha256_digest: Optional[str] = None
    blake2_256_digest: Optional[str] = None
    pyversion: Optional[str] = None
    content: Optional[UploadFile] = Field(exclude=True, default=None)
    filename: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.filename = self.content.filename

    @computed_field
    @property
    def index_path(self) -> str:
        return os.path.join(self.name, self.version, self.filename)

    @computed_field
    @property
    def metadata_path(self) -> str:
        return self.index_path + ".json"

    @computed_field
    @property
    def index_dir(self) -> str:
        return os.path.join(self.name, self.version)

    async def save(self, index: str) -> None:
        if not self.content:
            raise FileExistsError("Cannot overwrite an existing version.")

        if os.path.exists(os.path.join(index, self.index_path)):
            raise FileExistsError("Cannot overwrite an existing version.")

        os.makedirs(os.path.join(index, self.index_dir), exist_ok=True)

        with open(os.path.join(index, self.index_path), "wb") as file:
            file.write(await self.content.read())

        with open(os.path.join(index, self.metadata_path), "w") as file:
            file.write(self.model_dump_json())

    @classmethod
    def get_files(cls, index: str, name: str, version: str) -> list["FileMetadata"]:
        path = pathlib.Path(index, name, version)
        if not path.exists():
            raise FileNotFoundError(
                f"No package exists meeting the constraint {name}:{version}"
            )

        names = [str(i) for i in path.iterdir()]
        results = []
        for name in names:
            if not name.endswith(".json"):
                if name + ".json" in names:
                    with open(name, "r") as f:
                        results.append(FileMetadata(**json.load(f)))

        return results
