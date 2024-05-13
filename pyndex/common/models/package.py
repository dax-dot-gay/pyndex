from datetime import datetime
import os
from typing import Any, Optional
from pydantic import BaseModel, Field, computed_field, field_validator
from .file_meta import FileMetadata
from packaging.version import Version, parse

class PackageInfo(BaseModel):
    author: Optional[str] = None
    author_email: Optional[str] = None
    classifiers: Optional[list[str]] = None
    description: Optional[str] = None
    description_content_type: Optional[str] = None
    docs_url: Optional[str] = None
    download_url: Optional[str] = None
    home_page: Optional[str] = None
    keywords: Optional[str] = None
    license: Optional[str] = None
    maintainer: Optional[str] = None
    maintainer_email: Optional[str] = None
    name: str
    package_url: Optional[str] = None
    platform: Optional[str] = None
    project_url: Optional[str] = None
    project_urls: Optional[list[str]] = None
    release_url: Optional[str] = None
    requires_dist: Optional[list[str]] = None
    requires_python: Optional[str] = None
    summary: Optional[str] = None
    version: str
    yanked: bool = False
    yanked_reason: Optional[str] = None

    @field_validator("classifiers", "project_urls", "requires_dist", mode="before")
    @classmethod
    def ensure_list(cls, v: str | list[str] | dict[str, str]) -> list[str]:
        """Validates values to ensure they follow a standard format"""
        if type(v) == str:
            return [v]
        if type(v) == dict:
            return [key + ": " + val for key, val in v.items()]
        return v


class PackageDigests(BaseModel):
    md5: Optional[str] = None
    sha256: Optional[str] = None


class PackageUrl(BaseModel):
    comment_text: Optional[str] = None
    digests: PackageDigests
    filename: str
    packagetype: str
    python_version: str | None
    requires_python: Optional[str] = None
    size: int | None = None
    upload_time: datetime
    url: str
    yanked: bool = False
    yanked_reason: Optional[str] = None

    @computed_field
    @property
    def upload_time_iso_8601(self) -> str | None:
        if self.upload_time:
            return self.upload_time.isoformat(timespec="microseconds")
        return None

    @classmethod
    def from_meta(cls, meta: FileMetadata, url_base: str) -> "PackageUrl":
        """Generates from a FileMetadata object"""
        return PackageUrl(
            comment_text=meta.comment,
            digests=PackageDigests(
                md5=meta.md5_digest,
                sha256=meta.sha256_digest,
            ),
            filename=meta.filename,
            packagetype=meta.filetype,
            python_version=meta.pyversion,
            requires_python=meta.requires_python,
            upload_time=meta.upload_time,
            url=f"{url_base}/files/{meta.name}/{meta.version}/{meta.filename}",
        )


class APIMeta(BaseModel):
    api_version: str = Field(serialization_alias="api-version", default="1.1")


class PackageListItem(BaseModel):
    name: str


class PackageList(BaseModel):
    meta: APIMeta
    projects: list[PackageListItem]


class PackageFileDetail(BaseModel):
    filename: str
    url: str
    hashes: PackageDigests
    requires_python: Optional[str] = Field(
        serialization_alias="requires-python", default=None
    )
    dist_info_meta: Optional[bool | dict[str, str]] = Field(
        serialization_alias="dist-info-metadata", default=None
    )
    gpg_sig: Optional[bool] = Field(serialization_alias="gpg-sig", default=None)
    yanked: Optional[str | bool] = None

    @classmethod
    def from_meta(cls, meta: FileMetadata, url_base: str) -> "PackageFileDetail":
        """Generates from a FileMetadata object"""
        return PackageFileDetail(
            filename=meta.filename,
            url=f"{url_base}/files/{meta.name}/{meta.version}/{meta.filename}",
            hashes=PackageDigests(
                md5=meta.md5_digest,
                sha256=meta.sha256_digest,
            ),
            requires_python=meta.requires_python,
            dist_info_meta=True,
        )


class PackageDetail(BaseModel):
    meta: APIMeta
    name: str
    files: list[PackageFileDetail]


class Package(BaseModel):
    info: PackageInfo
    urls: list[PackageUrl]
    vulnerabilities: list[Any] = []
    versions: list[tuple[str, list[FileMetadata]]] = []
    local: bool = True

    @classmethod
    def assemble_package(
        cls,
        package_path: str,
        version: Optional[str] = None,
        url_base: str = "http://localhost:8000",
    ) -> "Package":
        """Generates a Package object from a package path

        Args:
            package_path (str): Package path
            version (Optional[str], optional): Package version. Defaults to None.
            url_base (str, optional): URL base for downloads. Defaults to "http://localhost:8000".

        Raises:
            KeyError: Raised if version is unknown

        Returns:
            Package: Assembled Package
        """

        # Order version & select requested/latest
        version_paths = {
            ver: os.path.join(package_path, ver) for ver in os.listdir(package_path)
        }
        versions = {
            ver: FileMetadata.get_files(path) for ver, path in version_paths.items()
        }
        ordered_versions = [
            str(i)
            for i in sorted([Version(ver) for ver in versions.keys()], reverse=True)
        ]
        if version:
            if not version in versions.keys():
                raise KeyError(f"Unknown version {version}")
        else:
            version = ordered_versions[0]

        info = PackageInfo(**versions[version][0].model_dump())
        urls = [PackageUrl.from_meta(meta, url_base) for meta in versions[version]]
        return Package(
            info=info,
            urls=urls,
            versions=[(version, versions[version]) for version in ordered_versions],
        )

    def detail(self, url_base: str = "http://localhost:8000") -> PackageDetail:
        """Returns package file detail

        Args:
            url_base (str, optional): File download base URL. Defaults to "http://localhost:8000".

        Returns:
            PackageDetail: Generated PackageDetail object
        """
        all_metas = []
        for version, metas in self.versions:
            all_metas.extend(metas)
        return PackageDetail(
            meta=APIMeta(),
            name=self.info.name,
            files=[PackageFileDetail.from_meta(ver, url_base) for ver in all_metas],
        )
