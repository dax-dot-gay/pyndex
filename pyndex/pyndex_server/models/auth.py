import base64
from functools import cached_property
from hashlib import pbkdf2_hmac
import os
from secrets import token_urlsafe
from typing import Any, Callable, Literal

from litestar import Request
from pydantic import BaseModel, Field
from tinydb import where

from .base import BaseObject
from litestar.connection import ASGIConnection
from litestar.exceptions import *
from litestar.handlers.base import BaseRouteHandler
from ...common import (
    AuthAdmin as _AuthAdmin,
    AuthGroup as _AuthGroup,
    AuthPermission as _AuthPermission,
    AuthUser as _AuthUser,
    AuthToken as _AuthToken,
    MetaPermission,
    PackagePermission,
)


class AuthBase:
    def permissions(self, project: str | None = None) -> list["AuthPermission"]:
        return AuthPermission.get_permissions(self, project=project)

    @cached_property
    def is_admin(self) -> bool:
        return any([i.permission == MetaPermission.ADMIN for i in self.permissions()])

    def check_access(self, project: str) -> PackagePermission | None:
        results = self.permissions(project=project)
        if len(results) == 0:
            return None

        bare = [i.permissions for i in results]
        if PackagePermission.MANAGE in bare:
            return PackagePermission.MANAGE
        elif PackagePermission.EDIT in bare:
            return PackagePermission.EDIT
        elif PackagePermission.VIEW in bare:
            return PackagePermission.VIEW
        return None


class AuthAdmin(_AuthAdmin, AuthBase):
    @property
    def id(self) -> str:
        return "_admin"


class AuthUser(_AuthUser, BaseObject, AuthBase):
    _collection = "creds"

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


class AuthGroup(_AuthGroup, BaseObject, AuthBase):
    _collection = "groups"

    def get_members(self) -> list["AuthUser | AuthToken"]:
        users = AuthUser.find(where("groups").any([self.id]))
        tokens = AuthToken.find(where("groups").any([self.id]))
        return [*users, *tokens]


class AuthToken(_AuthToken, BaseObject, AuthBase):
    _collection = "creds"

    @classmethod
    def from_token(cls, token: str) -> "AuthToken | None":
        return cls.find_one(where("token") == token)


class AuthPermission(_AuthPermission, BaseObject):
    _collection = "permissions"

    @classmethod
    def get_permissions(
        cls,
        target: AuthAdmin | AuthUser | AuthToken | AuthGroup | None,
        project: str | None = None,
    ) -> list["AuthPermission"]:
        if target == None:
            return []

        if isinstance(target, AuthGroup):
            target_type = "group"
            target_id = target.id
        else:
            target_type = "auth"
            target_id = target.id

        if project:
            results = AuthPermission.find(
                (where("target_type") == target_type)
                & (where("target_id") == target_id)
                & (where("project") == project)
            )
        else:
            results = AuthPermission.find(
                (where("target_type") == target_type)
                & (where("target_id") == target_id)
            )

        if isinstance(target, AuthAdmin):
            results.append(
                AuthPermission(
                    id="_admin",
                    permission=MetaPermission.ADMIN,
                    target_type="auth",
                    target_id="_admin",
                    project=project,
                )
            )
        return results


def get_authentication(
    request: Request, context: Any
) -> AuthAdmin | AuthToken | AuthUser | None:
    auth = request.headers.get("authorization")
    if auth == None:
        return None

    mode, encoded = auth.split(" ", maxsplit=1)
    if mode.lower() != "basic":
        raise ClientException(
            f"Incompatible authentication type {mode}. Only Basic is supported to maximize PEP compliance."
        )

    try:
        decoded = base64.b64decode(encoded).decode()
    except:
        raise ClientException("Failure to decode authentication data")

    username, password = decoded.split(":", maxsplit=1)
    if len(username) == 0:
        raise ClientException("A username must be provided")

    if username == "_token_":
        if not password:
            raise ClientException("An API token was not provided")

        result = AuthToken.from_token(password)
        if not result:
            raise NotAuthorizedException("Invalid API token provided")
        return result

    else:
        if (
            username == context.config.auth.admin.username
            and context.config.auth.admin.enabled
        ):
            if password != context.config.auth.admin.password:
                raise NotAuthorizedException("Invalid username or password")
            return AuthAdmin(username=context.config.auth.admin.username)

        result = AuthUser.from_username(username)
        if not result:
            raise NotAuthorizedException("Invalid username or password")

        if not result.verify(password):
            raise NotAuthorizedException("Invalid username or password")
        return result


async def guard_admin(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    auth = get_authentication(connection, connection.app.state.context)
    if not auth.is_admin:
        raise NotAuthorizedException(
            "Access to this endpoint is forbidden without the meta.admin permission."
        )
