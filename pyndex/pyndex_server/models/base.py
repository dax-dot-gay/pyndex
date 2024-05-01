from typing import ClassVar, Type, TypeVar
from uuid import uuid4
from pydantic import BaseModel, Field
from tinydb import Query, TinyDB, where
from tinydb.table import Table
import humps

TClass = TypeVar("TClass", bound="BaseObject")


class BaseObject(BaseModel):
    _db: ClassVar[TinyDB | None] = None
    _collection: ClassVar[str | None] = None
    id: str = Field(default_factory=lambda: uuid4().hex)

    @property
    def db(self) -> TinyDB:
        if self._db == None:
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
    def set_db(cls, db: TinyDB):
        cls._db = db

    @classmethod
    def find(cls: Type[TClass], query: Query) -> list[TClass]:
        return [cls(**i) for i in cls._db.table(cls._collection_name()).search(query)]

    @classmethod
    def find_one(cls: Type[TClass], query: Query) -> TClass | None:
        result = cls._db.table(cls._collection_name()).search(query)
        return cls(**result[0]) if len(result) > 0 else None

    @classmethod
    def get(cls: Type[TClass], id: str) -> TClass | None:
        result = cls._db.table(cls._collection_name()).get(where("id") == id)
        return cls(**result) if result else None

    @classmethod
    def exists(cls: Type[TClass], query: Query) -> bool:
        return cls._db.table(cls._collection_name()).contains(query)

    @classmethod
    def all(cls: Type[TClass]) -> list[TClass]:
        return [cls(**i) for i in cls._db.table(cls._collection_name()).all()]

    def save(self) -> None:
        self.table.upsert(self.model_dump(mode="json"), cond=where("id") == self.id)

    def delete(self) -> None:
        self.table.remove(cond=where("id") == self.id)


def initialize(db: TinyDB, objs: list[Type[BaseObject]]):
    for i in objs:
        i.set_db(db)
