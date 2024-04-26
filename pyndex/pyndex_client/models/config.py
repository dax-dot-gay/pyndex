from pydantic import BaseModel
import tomlkit


class PyndexIndex(BaseModel):
    name: str
    url: str
    username: str | bool = False
    password: str | bool = False
    token: str | bool = False


class PyndexConfig(BaseModel):
    default: str | bool = False
    index: dict[str, PyndexIndex] = {}

    @classmethod
    def from_file(cls, path: str) -> "PyndexConfig":
        with open(path, "rb") as f:
            return PyndexConfig(**tomlkit.load(f))

    def save(self, path: str):
        with open(path, "w") as f:
            return tomlkit.dump(self.model_dump(mode="json"))
