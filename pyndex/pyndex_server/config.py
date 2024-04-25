import tomllib
from typing import Optional
from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    root: str


class ApiConfig(BaseModel):
    path_base: str


class ProxyItemConfig(BaseModel):
    name: str
    priority: int
    url: str
    username: Optional[str] = None
    password: Optional[str] = None


class FeatureConfig(BaseModel):
    proxy: bool = True


class Config(BaseModel):
    storage: StorageConfig
    api: ApiConfig
    proxy: dict[str, ProxyItemConfig] = {}
    features: FeatureConfig = Field(default_factory=FeatureConfig)

    @classmethod
    def load(cls) -> "Config":
        with open("./config.toml", "rb") as config:
            return cls(**tomllib.load(config))

    @property
    def proxies(self) -> list[ProxyItemConfig]:
        if self.features.proxy:
            return sorted(list(self.proxy.values()), key=lambda x: x.priority)
        return []
