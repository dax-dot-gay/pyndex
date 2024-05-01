from typing import Any, Literal, Type
from litestar import Controller, get, post
from pydantic import BaseModel
from tinydb import where
from ..models import AuthAdmin, AuthUser, AuthToken, AuthGroup, guard_admin
from ..context import Context
from litestar.connection import ASGIConnection
from litestar.exceptions import *
from litestar.handlers.base import BaseRouteHandler


class RedactedAuth(BaseModel):
    id: str | None
    type: Literal["user", "token", "admin", "anonymous"]
    name: str | None
    groups: list[AuthGroup]
    linked: "RedactedAuth | None" = None

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


class MetaUserController(Controller):
    path = "/meta/users"
    guards = [guard_auth_enabled]

    @get(
        "/me",
    )
    async def get_self(self, auth: Any) -> RedactedAuth:
        return RedactedAuth.from_auth(auth)

    @get("/")
    async def list_users(self, context: Context) -> list[RedactedAuth]:
        results = AuthUser.all()
        if context.config.auth.admin.enabled:
            results.append(AuthAdmin(username=context.config.auth.admin.username))

        return [RedactedAuth.from_auth(r) for r in results]

    @get("/id/{id:str}")
    async def get_user_by_id(self, context: Context, id: str) -> RedactedAuth:
        if id == "_admin" and context.config.auth.admin.enabled:
            return RedactedAuth.from_auth(
                AuthAdmin(username=context.config.auth.admin.username)
            )
        else:
            result = AuthUser.get(id)
            if result:
                return result

        raise NotFoundException(f"User with ID {id} does not exist.")

    @get("/name/{username:str}")
    async def get_user_by_name(self, context: Context, username: str) -> RedactedAuth:
        if (
            context.config.auth.admin.enabled
            and username == context.config.auth.admin.username
        ):
            return RedactedAuth.from_auth(
                AuthAdmin(username=context.config.auth.admin.username)
            )
        else:
            result = AuthUser.from_username(username)
            if result:
                return result

        raise NotFoundException(f"User with username {username} does not exist.")

    @get("/me/admin")
    async def get_is_admin(self, auth: Any) -> bool:
        return auth.is_admin if auth else False


class UserCreationModel(BaseModel):
    username: str
    password: str | None = None


class GroupCreationModel(BaseModel):
    name: str
    display_name: str | None = None


class MetaAdminController(Controller):
    path = "/meta/admin"
    guards = [guard_admin, guard_auth_enabled]

    @post("/user")
    async def create_user(
        self, data: UserCreationModel, context: Context
    ) -> RedactedAuth:
        if (
            AuthUser.exists(where("username") == data.username)
            or data.username == context.config.auth.admin.username
        ):
            raise MethodNotAllowedException("User already exists.")

        created = AuthUser.create(data.username, password=data.password)
        created.save()
        return RedactedAuth.from_auth(created)

    @post("/user/{user_id:str}/groups")
    async def add_user_to_group(self, user_id: str, data: list[str]) -> RedactedAuth:
        user = AuthUser.get(user_id)
        if not user:
            raise NotFoundException("User ID not found")

        for group_name in data:
            group = AuthGroup.find_one(where("name") == group_name)
            if not group:
                raise NotFoundException(f"Group `{group_name}` not found")

            if not group.id in user.groups:
                user.groups.append(group.id)

        user.save()
        return RedactedAuth.from_auth(user)

    @post("/group")
    async def create_group(self, data: GroupCreationModel) -> AuthGroup:
        if AuthGroup.exists(where("name") == data.name):
            raise MethodNotAllowedException("Group already exists.")

        created = AuthGroup(name=data.name, display_name=data.display_name)
        created.save()
        return created


class MetaGroupController(Controller):
    path = "/meta/groups"
    guards = [guard_auth_enabled]

    @get("/")
    async def list_groups(self) -> list[AuthGroup]:
        return AuthGroup.all()

    @get("/{id:str}")
    async def get_group(self, id: str) -> AuthGroup:
        result = AuthGroup.get(id)
        if result:
            return result
        raise NotFoundException("Group ID not found")

    @get("/{id:str}/members")
    async def get_group_members(self, id: str) -> list[RedactedAuth]:
        return [
            RedactedAuth.from_auth(i)
            for i in [
                *AuthUser.find(where("groups").test(lambda groups: id in groups)),
                *AuthToken.find(where("groups").test(lambda groups: id in groups)),
            ]
        ]
