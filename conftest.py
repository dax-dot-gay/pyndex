from collections.abc import Iterator
from contextlib import contextmanager
import os
import shutil
from typing import Callable, Literal
from pyndex import server, Pyndex
from litestar.testing import TestClient
from httpx import BasicAuth
import pytest
from litestar import Litestar
from pydantic import BaseModel


class UserRequest(BaseModel):
    type: Literal["user"] = "user"
    username: str
    password: str | None = None
    groups: list[str] = []
    server_permissions: list[Literal["meta.admin", "meta.create"]] = []


class GroupRequest(BaseModel):
    type: Literal["group"] = "group"
    name: str
    display_name: str | None = None
    server_permissions: list[Literal["meta.admin", "meta.create"]] = []


USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "admin"

USERS = {"basic": "basic", "moderator": "moderator", "project_owner": "project_owner"}
GROUPS = {"basic": "Basic Group", "admins": "Administrators", "project_members": None}


@pytest.fixture(scope="class", autouse=True)
def env(tmp_path_factory: pytest.TempPathFactory, request):
    requests: list[UserRequest | GroupRequest] = []
    for request_type in ["user", "group"]:
        for req in request.node.iter_markers(name=request_type):
            match request_type:
                case "user":
                    requests.append(UserRequest(**req.kwargs))
                case "group":
                    requests.append(GroupRequest(**req.kwargs))

    directory = tmp_path_factory.mktemp("pynd_base")
    shutil.copyfile("./config.toml", "config.toml.dev")
    shutil.copyfile("./config.test.toml", "./config.toml")
    with open("config.toml", "r") as f:
        contents = f.read()
    (directory / "storage").mkdir(exist_ok=True)
    storage = (directory / "storage").absolute()

    with open("config.toml", "w") as f:
        f.write(contents.replace("{storage}", str(storage)))

    group_adds: dict[str, str] = {}
    with TestClient(app=server) as client:
        client.auth = BasicAuth(username=USERNAME_ADMIN, password=PASSWORD_ADMIN)
        with Pyndex("").session(client=client) as index:
            for req in requests:
                try:
                    match req.type:

                        case "user":
                            created = index.users.create(
                                req.username, password=req.password
                            )
                            if len(req.groups) > 0:
                                group_adds[created.id] = req.groups
                        case "group":
                            created = index.groups.create(
                                req.name, display_name=req.display_name
                            )
                except:
                    pass

            for user_id, group_names in group_adds.items():
                for name in group_names:
                    result = client.post(
                        f"/groups/name/{name}/members/add",
                        params={"auth_type": "user", "auth_id": user_id},
                    )
    yield directory
    shutil.copyfile("./config.toml.dev", "config.toml")
    os.remove("config.toml.dev")


@pytest.fixture(scope="function")
def admin_client(env) -> Iterator[TestClient[Litestar]]:
    with TestClient(app=server) as client:
        client.auth = BasicAuth(username=USERNAME_ADMIN, password=PASSWORD_ADMIN)
        yield client


@pytest.fixture(scope="function")
def as_admin(admin_client: TestClient) -> Iterator[Pyndex]:
    with Pyndex("").session(client=admin_client) as session:
        yield session


@pytest.fixture(scope="function")
def user_client(env) -> Callable[[str, str | None], Iterator[TestClient[Litestar]]]:
    @contextmanager
    def make_client(
        username: str, password: str | None
    ) -> Iterator[TestClient[Litestar]]:
        with TestClient(app=server) as client:
            client.auth = BasicAuth(
                username=username, password=password if password else None
            )
            yield client

    return make_client


@pytest.fixture(scope="function")
def as_user(env, user_client) -> Callable[[str, str | None], Iterator[Pyndex]]:
    @contextmanager
    def make_index(
        username: str, password: str | None
    ) -> Iterator[TestClient[Litestar]]:
        with user_client(username, password) as client:
            with Pyndex("").session(client=client) as index:
                yield index

    return make_index


@pytest.fixture
def admin_creds() -> tuple[str, str]:
    return USERNAME_ADMIN, PASSWORD_ADMIN
