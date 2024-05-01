from typing import Literal
from pydantic import BaseModel


class AuthUser(BaseModel):
    id: str
    type: Literal["user"] = "user"
    username: str | None = None
    password_hash: str | None = None
    password_salt: str | None = None
    groups: list[str] = []


class AuthGroup(BaseModel):
    id: str
    name: str
    display_name: str | None = None


class RedactedAuth(BaseModel):
    id: str | None
    type: Literal["user", "token", "admin", "anonymous"]
    name: str | None
    groups: list[AuthGroup]
    linked: AuthUser | None = None
