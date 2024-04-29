from contextlib import contextmanager
from typing import Any, Generator
from pydantic import BaseModel
import rich
from .config import PyndexConfig, PyndexIndex
from pyndex.common import Pyndex


class Context(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    repo_override: str | None = None
    verbosity: int = 0
    config_file_path: str
    config: PyndexConfig
    console: rich.console.Console

    @property
    def repo(self) -> PyndexIndex | None:
        if self.repo_override:
            try:
                return self.config.index[self.repo_override]
            except KeyError:
                return None

        else:
            if not self.config.default:
                return None
            try:
                return self.config.index[self.config.default]
            except KeyError:
                return None

    @contextmanager
    def index(self) -> Generator[Pyndex | None, Any, None]:
        repo = self.repo
        if repo:
            with Pyndex(
                repo.url,
                username=repo.username,
                password=repo.password,
                token=repo.token,
            ) as index:
                yield index

        else:
            yield None
