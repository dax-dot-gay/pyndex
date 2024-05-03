from typing import Any, Literal, Type
from litestar import Controller, get, post
from pydantic import BaseModel
from tinydb import where
from ..models import AuthAdmin, AuthUser, AuthToken, AuthGroup, guard_admin
from ..context import Context
from litestar.connection import ASGIConnection
from litestar.exceptions import *
from litestar.status_codes import *
from litestar.handlers.base import BaseRouteHandler


class RedactedAuth(BaseModel):
    id: str | None
    type: Literal["user", "token", "admin", "anonymous"]
    name: str | None
    groups: list[AuthGroup]
    linked: "RedactedAuth | None" = None

    @classmethod
    def from_auth(
        cls: "Type[RedactedAuth]", auth: AuthAdmin | AuthUser | AuthToken | None
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
                    groups=AuthGroup.find(where("id").one_of(auth.groups)),
                    linked=AuthUser.get(auth.linked_user),
                )
            case "user":
                return cls(
                    id=auth.id,
                    type="user",
                    name=auth.username,
                    groups=AuthGroup.find(where("id").one_of(auth.groups)),
                )


def guard_auth_enabled(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.app.state.context.config.features.auth:
        raise NotFoundException(
            "Endpoint disabled (auth/user management is not configured)"
        )


class UserCreationModel(BaseModel):
    username: str
    password: str | None = None


class UserController(Controller):
    path = "/users"
    guards = [guard_auth_enabled]

    @get("/")
    async def get_all_users(self, context: Context) -> list[RedactedAuth]:
        results = AuthUser.all()
        if context.config.auth.admin.enabled:
            results.append(AuthAdmin(username=context.config.auth.admin.username))

        return [RedactedAuth.from_auth(auth) for auth in results]

    @get("/self")
    async def get_self(self, auth: Any) -> RedactedAuth:
        return RedactedAuth.from_auth(auth)

    @get("/id/{user_id:str}")
    async def get_user_by_id(self, user_id: str, context: Context) -> RedactedAuth:
        if user_id == "_admin":
            if context.config.auth.admin.enabled:
                return RedactedAuth.from_auth(
                    AuthAdmin(username=context.config.auth.admin.username)
                )
            else:
                raise NotFoundException("Unknown user ID")

        result = AuthUser.get(user_id)
        if result:
            return RedactedAuth.from_auth(result)
        raise NotFoundException("Unknown user ID")

    @get("/name/{username:str}")
    async def get_user_by_name(self, username: str, context: Context) -> RedactedAuth:
        if username == context.config.auth.admin.username:
            if context.config.auth.admin.enabled:
                return RedactedAuth.from_auth(
                    AuthAdmin(username=context.config.auth.admin.username)
                )
            else:
                raise NotFoundException("Unknown username")

        result = AuthUser.from_username(username)
        if result:
            return RedactedAuth.from_auth(result)
        raise NotFoundException("Unknown username")

    @post("/create", guards=[guard_admin])
    async def create_user(
        self, context: Context, data: UserCreationModel
    ) -> RedactedAuth:
        if data.username == context.config.auth.admin.username:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail="Conflict with existing username"
            )

        if AuthUser.exists(where("username") == data.username):
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail="Conflict with existing username"
            )

        created = AuthUser.create(data.username, password=data.password)
        created.save()
        return RedactedAuth.from_auth(created)
