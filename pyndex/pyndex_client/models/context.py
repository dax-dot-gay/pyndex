from pydantic import BaseModel
from .config import PyndexConfig


class Context(BaseModel):
    verbosity: int = 0
    config_file_path: str
    config: PyndexConfig
