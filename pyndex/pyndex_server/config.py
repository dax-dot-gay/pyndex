import tomllib
from typing import Literal
from pydantic import BaseModel


class DatabaseSqliteConfig(BaseModel):
    engine: Literal["sqlite"]
    path: str


class StorageConfig(BaseModel):
    root: str
    database: DatabaseSqliteConfig


class ApiConfig(BaseModel):
    path_base: str


class Config(BaseModel):
    storage: StorageConfig
    api: ApiConfig

    @classmethod
    def load(cls) -> "Config":
        with open("./config.toml", "rb") as config:
            return cls(**tomllib.load(config))
