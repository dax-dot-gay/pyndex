from hashlib import pbkdf2_hmac
import os
from secrets import token_urlsafe
from typing import Literal

from pydantic import BaseModel, Field
from tinydb import where
from .base import BaseObject


class AuthAdmin(BaseModel):
    type: Literal["admin"] = "admin"
    username: str


class AuthUser(BaseObject):
    _collection = "creds"
    type: Literal["user"] = "user"
    username: str
    password_hash: str | None
    password_salt: str | None
    groups: list[str] = []

    @classmethod
    def create(cls, username: str, password: str | None = None) -> "AuthUser":
        if password:
            password_salt = os.urandom(32).hex()
            password_hash = pbkdf2_hmac(
                "sha256", password.encode(), bytes.fromhex(password_salt), 100000
            ).hex()
        else:
            password_salt = None
            password_hash = None

        return AuthUser(
            username=username, password_hash=password_hash, password_salt=password_salt
        )

    def verify(self, password: str | None) -> bool:
        if password == None or password == "":
            return self.password_hash == None

        return (
            pbkdf2_hmac(
                "sha256", password.encode(), bytes.fromhex(self.password_salt), 100000
            ).hex()
            == self.password_hash
        )

    @classmethod
    def from_username(cls, username: str) -> "AuthUser | None":
        return cls.find_one(where("username") == username)


class AuthGroup(BaseObject):
    _collection = "groups"
    name: str
    display_name: str | None = None


class AuthToken(BaseObject):
    _collection = "creds"
    token: str = Field(default_factory=lambda: token_urlsafe())
    type: Literal["token"] = "token"
    linked_user: str | None = None
    description: str | None = None

    @classmethod
    def from_token(cls, token: str) -> "AuthToken | None":
        return cls.find_one(where("token") == token)
