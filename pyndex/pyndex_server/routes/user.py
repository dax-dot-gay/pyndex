from typing import Any, Literal, Type
from litestar import Controller, delete, get, post
from pydantic import BaseModel
from tinydb import where
from ..models import AuthAdmin, AuthUser, AuthToken, AuthGroup, guard_admin
from ..context import Context
from litestar.connection import ASGIConnection
from litestar.exceptions import *
from litestar.status_codes import *
from litestar.handlers.base import BaseRouteHandler
from litestar.di import Provide


class RedactedAuth(BaseModel):
    """
    Generalized wrapper around auth types that redacts sensitive information for network transmission.

    Attributes:
        id (str | None): Auth ID
        type (Literal["user" | "token", "admin", "anonymous"]): Auth type
        name (str | None): Identifying information about the auth object. For instance, users will use their username here, and tokens will use their description.
        groups (list[AuthGroup]): A list of AuthGroups that the auth object is a member of
        linked (RedactedAuth | None): The linked user, in the case of an API token.
    """
    id: str | None
    type: Literal["user", "token", "admin", "anonymous"]
    name: str | None
    groups: list[AuthGroup]
    linked: "RedactedAuth | None" = None

    @classmethod
    def from_auth(
        cls: "Type[RedactedAuth]", auth: AuthAdmin | AuthUser | AuthToken | None
    ) -> "RedactedAuth":
        """Creates a RedactedAuth from an auth object.

        Args:
            auth (AuthAdmin | AuthUser | AuthToken | None): Auth object to create from (or None for anon)

        Returns:
            RedactedAuth: Generated RedactedAuth object
        """
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
    """Rejects connection if auth isn't enabled in the server config."""
    if not connection.app.state.context.config.features.auth:
        raise NotFoundException(
            "Endpoint disabled (auth/user management is not configured)"
        )


class UserCreationModel(BaseModel):
    username: str
    password: str | None = None


class UserController(Controller):
    """Manages user interactions not specific to a single user."""
    path = "/users"
    guards = [guard_auth_enabled]

    @get("/")
    async def get_all_users(self, context: Context) -> list[RedactedAuth]:
        """Returns a list of all users (not API tokens)

        Args:
            context (Context): Application context

        Returns:
            list[RedactedAuth]: A list of RedactedAuth objects
        """
        results = AuthUser.all()
        if context.config.auth.admin.enabled:
            results.append(AuthAdmin(username=context.config.auth.admin.username))

        return [RedactedAuth.from_auth(auth) for auth in results]

    @post("/create", guards=[guard_admin])
    async def create_user(
        self, context: Context, data: UserCreationModel
    ) -> RedactedAuth:
        """Creates a user given a username & password in request data.

        Args:
            context (Context): Application context
            data (UserCreationModel): JSON containing username & optional password

        Raises:
            HTTPException: If the username is already in use

        Returns:
            RedactedAuth: Created user
        """
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


async def provide_user_query(
    method: Literal["name", "id"], value: str, context: Context
) -> AuthUser | AuthAdmin:
    """Gets a user based on either username or ID. Used as a dependency.

    Args:
        method (Literal[&quot;name&quot;, &quot;id&quot;]): Whether to use user ID or username to query users
        value (str): Value to query by (id or username)
        context (Context): Application context

    Returns:
        AuthUser | AuthAdmin: Retrieved user
    """
    if not method in ["name", "id"]:
        raise ValidationException(f"Unknown query method `{method}`")

    if method == "name":
        if value == context.config.auth.admin.username:
            if context.config.auth.admin.enabled:
                return AuthAdmin(username=context.config.auth.admin.username)
            else:
                raise NotFoundException("Unknown username")

        result = AuthUser.from_username(value)
        if result:
            return result
        raise NotFoundException("Unknown username")
    else:
        if value == "_admin":
            if context.config.auth.admin.enabled:
                return AuthAdmin(username=context.config.auth.admin.username)
            else:
                raise NotFoundException("Unknown user ID")

        result = AuthUser.get(value)
        if result:
            return result
        raise NotFoundException("Unknown user ID")


class UserSelfController(Controller):
    """Operations pertaining to the currently logged-in user"""
    path = "/users/self"
    guards = [guard_auth_enabled]

    @get("/")
    async def get_self(self, auth: Any) -> RedactedAuth:
        """Returns the currently active user

        Args:
            auth (Any): Currently authenticated user (dependency)

        Returns:
            RedactedAuth: Active user info
        """
        return RedactedAuth.from_auth(auth)


class UserQueryController(Controller):
    """Operations on specified users via `provide_user_query()`"""
    path = "/users/{method:str}/{value:str}"
    guards = [guard_auth_enabled]
    dependencies = {"user": Provide(provide_user_query)}

    @get("/")
    async def get_user(self, user: Any) -> RedactedAuth:
        """Returns info about the queried user

        Args:
            user (Any): Queried user result

        Returns:
            RedactedAuth: Queried user info
        """
        return RedactedAuth.from_auth(user)

    @delete("/", guards=[guard_admin])
    async def delete_user(self, user: Any) -> None:
        user.delete()
