import os
import pathlib
from .config import Config
from .models import *
import tinydb


class Context:
    def __init__(self, config: Config) -> None:
        self.config = config

        os.makedirs(self.config.storage.root, exist_ok=True)
        self.root = pathlib.Path(self.config.storage.root)
        self.root.joinpath("index").mkdir(exist_ok=True, parents=True)
        self.db = tinydb.TinyDB(str(self.root.joinpath("pyndex.json")))
        initialize(self.db, [AuthGroup, AuthToken, AuthUser, AuthPermission])
