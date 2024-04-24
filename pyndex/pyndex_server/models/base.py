from typing import ClassVar, Type, TypeVar
from uuid import uuid4
from pydantic import BaseModel, Field
from tinydb import TinyDB, where
from tinydb.table import Table
import humps

TClass = TypeVar("TClass", bound="BaseObject")


class BaseObject(BaseModel):
    _db: ClassVar[TinyDB | None] = None
    _collection: ClassVar[str | None] = None
    id: str = Field(default_factory=lambda: uuid4())

    @property
    def db(self) -> TinyDB:
        if not self._db:
            raise RuntimeError("Database was not initialized")

        return self._db

    @property
    def collection(self) -> str:
        if self._collection:
            return self._collection

        return humps.camelize(self.__class__.__name__)

    @property
    def table(self) -> Table:
        return self.db.table(self.collection)

    @classmethod
    def _collection_name(cls) -> str:
        if cls._collection:
            return cls._collection

        return humps.camelize(cls.__name__)

    @classmethod
    def get(cls: Type[TClass], id: str) -> TClass | None:
        return cls._db.table(cls._collection_name()).get(where("id") == id)

    def save(self) -> None:
        self.table.upsert(self.model_dump(mode="json"), cond=where("id") == self.id)

    def delete(self) -> None:
        self.table.remove(cond=where("id") == self.id)
