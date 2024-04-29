from typing import Literal
from pydantic import BaseModel


class RedactedAuth(BaseModel):
    id: str | None
    type: Literal["user", "token", "admin", "anonymous"]
    name: str | None
    groups: list[str]
    linked: str | None = None
