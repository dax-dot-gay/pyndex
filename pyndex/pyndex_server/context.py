import os
import pathlib
from .config import Config
from piccolo.engine import SQLiteEngine, PostgresEngine


class Context:
    def __init__(self, config: Config) -> None:
        self.config = config

        os.makedirs(self.config.storage.root, exist_ok=True)
        self.root = pathlib.Path(self.config.storage.root)
        self.root.joinpath("index").mkdir(exist_ok=True, parents=True)

        self.db = None
        match self.config.storage.database.engine:
            case "sqlite":
                self.db = SQLiteEngine(path=self.config.storage.database.path)
            case "postgres":
                raise NotImplementedError
