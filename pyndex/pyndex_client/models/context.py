from contextlib import contextmanager
import json
import os
from typing import Any, Generator
import click
from pydantic import BaseModel
from ...pyndex_api import Pyndex
from rich.console import Console


class ConfigEntry(BaseModel):
    name: str
    host: str
    base_url: str | None = None
    username: str | None = None
    password: str | None = None


class Config(BaseModel):
    _file: str
    repositories: dict[str, ConfigEntry] = {}
    default: str | None = None

    def __init__(self, file: str, **data):
        super().__init__(**data)
        self._file = file

    @classmethod
    def load(cls, path: str) -> "Config":
        if path == "-" or os.path.exists(path):
            with click.open_file(path) as f:
                return Config(path, **json.load(f))

        else:
            return Config(path)

    def save(self) -> None:
        if self._file != "-":
            with click.open_file(self._file, "w") as f:
                f.write(self.model_dump_json(indent=4))


class AppContext(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    repo: ConfigEntry | None
    config: Config
    client: Pyndex | None
    console: Console

    @classmethod
    @contextmanager
    def create(
        cls, config_path: str, repository: str | None = None
    ) -> Generator["AppContext", Any, Any]:
        config = Config.load(config_path)
        repo = (
            config.repositories[repository]
            if repository
            else (config.repositories[config.default] if config.default else None)
        )
        if repo:
            with Pyndex(
                repo.host,
                api_base=repo.base_url,
                username=repo.username,
                password=repo.username,
            ) as index:
                yield AppContext(
                    repo=repo,
                    config=config,
                    client=index,
                    console=Console(highlight=False),
                )
        else:
            yield AppContext(
                repo=None, config=config, client=None, console=Console(highlight=False)
            )

        config.save()

    def error(self, message: str):
        self.console.print(f"[bold red]Error:[/bold red] {message}")
