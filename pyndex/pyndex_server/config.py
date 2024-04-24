import tomllib
from pydantic import BaseModel


class StorageConfig(BaseModel):
    root: str


class ApiConfig(BaseModel):
    path_base: str


class Config(BaseModel):
    storage: StorageConfig
    api: ApiConfig

    @classmethod
    def load(cls) -> "Config":
        with open("./config.toml", "rb") as config:
            return cls(**tomllib.load(config))
