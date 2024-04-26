from secrets import token_urlsafe
from typing import Literal

from pydantic import Field
from .base import BaseObject


class AuthUser(BaseObject):
    _collection = "creds"
    type: Literal["user"] = "user"
    username: str
    password: str | None
    groups: list[str] = []


class AuthGroup(BaseObject):
    _collection = "groups"
    name: str
    display_name: str | None = None


class AuthToken(BaseObject):
    _collection = "creds"
    token: str = Field(default_factory=lambda: token_urlsafe())
    type: Literal["token"] = "token"
    linked_user: str | None = None
