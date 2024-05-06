from collections.abc import Iterator
import os
import shutil
from pyndex import server, Pyndex
from litestar.testing import TestClient
from httpx import BasicAuth
import pytest
from litestar import Litestar


USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "admin"

USERNAME_REGULAR = "regular"
PASSWORD_REGULAR = "regular"


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
    yield directory
    shutil.copyfile("./config.toml.dev", "config.toml")
    os.remove("config.toml.dev")


@pytest.fixture(scope="class")
def admin_client(env) -> Iterator[TestClient[Litestar]]:
    with TestClient(app=server) as client:
        client.auth = BasicAuth(username=USERNAME_ADMIN, password=PASSWORD_ADMIN)
        yield client


@pytest.fixture(scope="class")
def user_client(env) -> Iterator[TestClient[Litestar]]:
    with TestClient(app=server) as client:
        client.auth = BasicAuth(username=USERNAME_REGULAR, password=PASSWORD_REGULAR)
        yield client


@pytest.fixture(scope="function")
def as_admin(admin_client: TestClient) -> Iterator[Pyndex]:
    with Pyndex("").session(client=admin_client) as session:
        yield session


@pytest.fixture(scope="function")
def as_user(user_client: TestClient) -> Iterator[Pyndex]:
    with Pyndex("").session(client=user_client) as session:
        yield session
