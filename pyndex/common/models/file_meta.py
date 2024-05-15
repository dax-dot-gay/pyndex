from datetime import UTC, datetime
import json
import os
import pathlib
from typing import Optional
from pydantic import BaseModel, Field, computed_field
from litestar.datastructures import UploadFile

FIELD_MAP = {
    "project_url": "Project-URL",
    "project_urls": "Project-URL",
    "classifiers": "Classifier",
}


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
    project_url: Optional[list[str]] = None
    project_urls: Optional[list[str]] = None
    provides_dist: Optional[list[str]] = None
    obsoletes_dist: Optional[list[str]] = None
    provides: Optional[list[str]] = None
    requires: Optional[list[str]] = None
    obsoletes: Optional[list[str]] = None
    comment: Optional[str] = None
    action: str = Field(validation_alias=":action", default="file_upload")
    protocol_version: int
    filetype: Optional[str] = None
    md5_digest: Optional[str] = None
    sha256_digest: Optional[str] = None
    blake2_256_digest: Optional[str] = None
    pyversion: Optional[str] = None
    content: Optional[UploadFile] = Field(exclude=True, default=None)
    filename: Optional[str] = None
    upload_time: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.content:
            self.filename = self.content.filename
            self.upload_time = datetime.now(tz=UTC)

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
        """Saves metadata to sidecar file

        Args:
            index (str): Index root folder

        Raises:
            FileExistsError: Raised if the version already exists or if no content was provided.
        """
        if not self.content:
            raise FileExistsError("No content was provided")

        if os.path.exists(os.path.join(index, self.index_path)):
            raise FileExistsError("Cannot overwrite an existing version.")

        os.makedirs(os.path.join(index, self.index_dir), exist_ok=True)

        with open(os.path.join(index, self.index_path), "wb") as file:
            file.write(await self.content.read())

        with open(os.path.join(index, self.metadata_path), "w") as file:
            file.write(self.model_dump_json())

    @classmethod
    def get_files(cls, path: str) -> list["FileMetadata"]:
        """Gets all file metadata associated with a package version

        Raises:
            FileNotFoundError: Raised if the package is unknown

        Returns:
            list[FileMetadata]: List of file metadata
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Package directory '{path}' does not exist.")

        names = [str(i) for i in os.listdir(path)]
        results = []
        for name in names:
            if not name.endswith(".json"):
                if name + ".json" in names:
                    with open(os.path.join(path, name + ".json"), "r") as f:
                        data = json.load(f)
                        results.append(FileMetadata(**data))

        return results

    def as_metadata(self) -> str:
        """Converts to PYPA metadata format"""
        output = ""
        for key, value in self.model_dump(
            mode="json", exclude={"index_path", "metadata_path", "index_dir"}
        ).items():
            if value:
                if key in FIELD_MAP.keys():
                    field_name = FIELD_MAP[key]
                else:
                    field_name = key.title().replace("_", "-")

                if type(value) == list:
                    for i in value:
                        output += field_name + ": " + i + "\n"
                else:
                    output += field_name + ": " + str(value) + "\n"
        return output
