from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


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


class PackageDigests(BaseModel):
    blake2b_256: Optional[str] = None
    md5: Optional[str] = None
    sha256: Optional[str] = None


class PackageUrl(BaseModel):
    comment_text: Optional[str] = None
    digests: PackageDigests
    filename: str
    packagetype: str
    python_version: str
    requires_python: Optional[str] = None
    size: int
    upload_time: datetime
    url: str
    yanked: bool = False
    yanked_reason: Optional[str] = None


class Package(BaseModel):
    info: PackageInfo
    urls: list[PackageUrl]
    vulnerabilities: list[Any] = []
