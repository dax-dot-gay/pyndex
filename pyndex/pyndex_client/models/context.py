from pydantic import BaseModel
from .config import PyndexConfig, PyndexIndex


class Context(BaseModel):
    repo_override: str | None = None
    verbosity: int = 0
    config_file_path: str
    config: PyndexConfig

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
