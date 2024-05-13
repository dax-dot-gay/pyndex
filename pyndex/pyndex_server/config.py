import os
import tomllib
from typing import Optional
from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    root: str


class ApiConfig(BaseModel):
    path_base: str


class ProxyItemUrls(BaseModel):
    index: str
    package: Optional[str] = None


class ProxyItemConfig(BaseModel):
    name: str
    priority: int
    username: Optional[str] = None
    password: Optional[str] = None
    urls: ProxyItemUrls


class FeatureConfig(BaseModel):
    proxy: bool = True
    auth: bool = True


class AuthAdminConfig(BaseModel):
    username: str
    password: str
    enabled: bool = True


class AuthenticationConfig(BaseModel):
    admin: AuthAdminConfig | None = None


class Config(BaseModel):
    storage: StorageConfig
    api: ApiConfig
    proxy: dict[str, ProxyItemConfig] = {}
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    auth: AuthenticationConfig

    @classmethod
    def load(cls) -> "Config":
        with open(os.getenv("PYNDEX_CONFIG", "./config.toml"), "rb") as config:
            return cls(**tomllib.load(config))

    @property
    def proxies(self) -> list[ProxyItemConfig]:
        if self.features.proxy:
            return sorted(list(self.proxy.values()), key=lambda x: x.priority)
        return []
