from collections.abc import Iterator
import shutil
from pyndex import server, Pyndex
from litestar.testing import TestClient
from httpx import BasicAuth
import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar import Litestar

USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "admin"

USERNAME_REGULAR = "regular"
PASSWORD_REGULAR = "regular"


@pytest.fixture(scope="class")
def env(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch):
    directory = tmp_path_factory.mktemp("pynd_base")
    shutil.copyfile("./config.test.toml", directory / "config.toml")
    with open(directory / "config.toml", "r") as f:
        contents = f.read()
    (directory / "storage").mkdir(exist_ok=True)
    storage = (directory / "storage").absolute()

    with open(directory / "config.toml", "w") as f:
        f.write(contents.format(storage=str(storage)))
    monkeypatch.setenv("PYNDEX_CONFIG", str((directory / "config.toml").absolute()))
    return directory


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
