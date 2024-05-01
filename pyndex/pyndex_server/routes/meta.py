from typing import Any, Literal, Type
from litestar import Controller, get
from pydantic import BaseModel
from ..models import AuthAdmin, AuthUser, AuthToken
from ..context import Context
from litestar.connection import ASGIConnection
from litestar.exceptions import *
from litestar.handlers.base import BaseRouteHandler


class RedactedAuth(BaseModel):
    id: str | None
    type: Literal["user", "token", "admin", "anonymous"]
    name: str | None
    groups: list[str]
    linked: str | None = None

    @classmethod
    def from_auth(
        cls: "Type[RedactedAuth]", auth: AuthAdmin | AuthUser | AuthToken
    ) -> "RedactedAuth":
        if auth == None:
            return cls(id=None, type="anonymous", name=None, groups=[])

        match auth.type:
            case "admin":
                return cls(id="_admin", type="admin", name=auth.username, groups=[])
            case "token":
                return cls(
                    id=auth.id,
                    type="token",
                    name=auth.description,
                    groups=auth.groups,
                    linked=auth.linked_user,
                )
            case "user":
                return cls(
                    id=auth.id, type="user", name=auth.username, groups=auth.groups
                )


def guard_auth_enabled(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.app.state.context.config.features.auth:
        raise NotFoundException(
            "Endpoint disabled (auth/user management is not configured)"
        )


class MetaUserController(Controller):
    path = "/meta/users"

    @get(
        "/me",
    )
    async def get_self(self, auth: Any) -> RedactedAuth:
        return RedactedAuth.from_auth(auth)

    @get("/")
    async def list_users(self, context: Context) -> list[RedactedAuth]:
        if context.config.features.auth:
            results = AuthUser.all()
            if context.config.auth.admin.enabled:
                results.append(AuthAdmin(username=context.config.auth.admin.username))

            return [RedactedAuth.from_auth(r) for r in results]

        return []
