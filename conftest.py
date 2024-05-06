from collections.abc import Iterator
from contextlib import contextmanager
import os
import shutil
from typing import Callable
from pyndex import server, Pyndex
from litestar.testing import TestClient
from httpx import BasicAuth
import pytest
from litestar import Litestar


USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "admin"

USERS = {"basic": "basic", "moderator": "moderator", "project_owner": "project_owner"}
GROUPS = {"basic": "Basic Group", "admins": "Administrators", "project_members": None}


@pytest.fixture(scope="class", autouse=True)
def env(tmp_path_factory: pytest.TempPathFactory):
    directory = tmp_path_factory.mktemp("pynd_base")
    shutil.copyfile("./config.toml", "config.toml.dev")
    shutil.copyfile("./config.test.toml", "./config.toml")
    with open("config.toml", "r") as f:
        contents = f.read()
    (directory / "storage").mkdir(exist_ok=True)
    storage = (directory / "storage").absolute()

    with open("config.toml", "w") as f:
        f.write(contents.replace("{storage}", str(storage)))

    with TestClient(app=server) as client:
        client.auth = BasicAuth(username=USERNAME_ADMIN, password=PASSWORD_ADMIN)
        with Pyndex("").session(client=client) as index:
            for username, password in USERS.items():
                index.users.create(username, password=password)

            for name, display in GROUPS.items():
                index.groups.create(name, display_name=display)
    yield directory
    shutil.copyfile("./config.toml.dev", "config.toml")
    os.remove("config.toml.dev")


@pytest.fixture(scope="function")
def admin_client(env) -> Iterator[TestClient[Litestar]]:
    with TestClient(app=server) as client:
        client.auth = BasicAuth(username=USERNAME_ADMIN, password=PASSWORD_ADMIN)
        yield client


@pytest.fixture(scope="function")
def user_client(env, request) -> Iterator[TestClient[Litestar]]:
    mark = request.node.get_closest_marker("user")
    print(dir(request.node))
    if mark:
        username = mark.args[0]
        if username in USERS.keys():
            password = USERS[username]
        else:
            raise KeyError(f"Undefined user {username}")
    else:
        username = "basic"
        password = "basic"
    with TestClient(app=server) as client:
        client.auth = BasicAuth(username=username, password=password)
        yield client


@pytest.fixture(scope="function")
def dynamic_user(env) -> Callable[[str], Iterator[TestClient[Litestar]]]:
    @contextmanager
    def make_client(user: str) -> Iterator[TestClient[Litestar]]:
        if user in USERS.keys():
            with TestClient(app=server) as client:
                client.auth = BasicAuth(username=user, password=USERS[user])
                yield client
        else:
            raise KeyError

    return make_client


@pytest.fixture(scope="function")
def as_admin(admin_client: TestClient) -> Iterator[Pyndex]:
    with Pyndex("").session(client=admin_client) as session:
        yield session


@pytest.fixture(scope="function")
def as_user(user_client: TestClient) -> Iterator[dict[str, Pyndex]]:
    with Pyndex("").session(client=user_client) as session:
        yield session


@pytest.fixture(scope="function")
def as_dynamic_user(dynamic_user) -> Callable[[str], Iterator[Pyndex]]:
    @contextmanager
    def make_index(user: str) -> Iterator[Pyndex]:
        with dynamic_user(user) as client:
            with Pyndex("").session(client=client) as index:
                yield index

    return make_index


@pytest.fixture
def admin_creds() -> tuple[str, str]:
    return USERNAME_ADMIN, PASSWORD_ADMIN


@pytest.fixture
def user_creds() -> dict[str, str | None]:
    return USERS
