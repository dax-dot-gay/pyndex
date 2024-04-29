import json
from pydantic import BaseModel, field_serializer, field_validator
import tomlkit


class PyndexIndex(BaseModel):
    name: str
    url: str
    username: str | None = None
    password: str | None = None
    token: str | None = None

    @field_serializer(
        "username", "password", "token", when_used="always", return_type=bool | str
    )
    def ser_nones(self, v: str | None) -> bool | str:
        if v == None:
            return False
        return v

    @field_validator("username", "password", "token", mode="before")
    @classmethod
    def val_nones(cls, v: str | bool) -> str | None:
        if type(v) == str:
            return v
        return None


class PyndexConfig(BaseModel):
    default: str | None = None
    index: dict[str, PyndexIndex] = {}

    @field_serializer("default", when_used="always", return_type=bool | str)
    def ser_default(self, v: str | None) -> bool | str:
        if v == None:
            return False
        return v

    @field_validator("default", mode="before")
    @classmethod
    def val_default(cls, v: str | bool) -> str | None:
        if type(v) == str:
            return v
        return None

    @classmethod
    def from_file(cls, path: str) -> "PyndexConfig":
        with open(path, "rb") as f:
            return PyndexConfig(**json.loads(json.dumps(tomlkit.load(f))))

    def save(self, path: str):
        with open(path, "w") as f:
            ser = tomlkit.dumps(self.model_dump(mode="json"))
            f.write(ser)
