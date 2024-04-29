import base64
from httpx import Request
from litestar import Router
from litestar.di import Provide
from .pypi import PypiController
from .files import FilesController
from .packages import PackagesController
from ..context import Context
from ..models import AuthUser, AuthToken, AuthAdmin
from litestar.connection import ASGIConnection
from litestar.exceptions import *
from litestar.handlers.base import BaseRouteHandler


async def guard_authenticated(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    context: Context = connection.app.state.context
    if context.config.features.auth:
        if not connection.headers.get("authorization", None):
            raise NotAuthorizedException(
                "This endpoint requires authentication.",
                headers={"WWW-Authenticate": "Basic"},
            )

        mode, encoded = connection.headers["authorization"].split(" ", maxsplit=1)
        if mode.lower() != "basic":
            raise NotAuthorizedException(
                f"Incompatible authentication type {mode}. Only Basic is supported to maximize PEP compliance.",
                headers={"WWW-Authenticate": "Basic"},
            )

        try:
            decoded = base64.b64decode(encoded).decode()
        except:
            raise ClientException("Failure to decode authentication data")

        username, password = decoded.split(":", maxsplit=1)
        if len(username) == 0:
            raise NotAuthorizedException(
                "A username must be provided", headers={"WWW-Authenticate": "Basic"}
            )

        if username == "_token_":
            if not password:
                raise NotAuthorizedException(
                    "An API token was not provided",
                    headers={"WWW-Authenticate": "Basic"},
                )

            result = AuthToken.from_token(password)
            if not result:
                raise NotAuthorizedException(
                    "Invalid API token provided", headers={"WWW-Authenticate": "Basic"}
                )

        else:
            if (
                username == context.config.auth.admin.username
                and context.config.auth.admin.enabled
            ):
                if password != context.config.auth.admin.password:
                    raise NotAuthorizedException(
                        "Invalid username or password",
                        headers={"WWW-Authenticate": "Basic"},
                    )
                return

            result = AuthUser.from_username(username)
            if not result:
                raise NotAuthorizedException(
                    "Invalid username or password",
                    headers={"WWW-Authenticate": "Basic"},
                )

            if not result.verify(password):
                raise NotAuthorizedException(
                    "Invalid username or password",
                    headers={"WWW-Authenticate": "Basic"},
                )


async def provide_authentication(
    request: Request, context: Context
) -> AuthToken | AuthUser | AuthAdmin | None:
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


def make_api_router(base: str) -> Router:
    return Router(
        base,
        route_handlers=[PypiController, FilesController, PackagesController],
        guards=[guard_authenticated],
        dependencies={"auth": Provide(provide_authentication)},
    )
