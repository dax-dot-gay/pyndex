from litestar.testing import TestClient
import pytest


class TestAdmin:
    def test_admin_self(self, admin_client: TestClient, admin_creds: tuple[str, str]):
        result = admin_client.get("/users/self")
        assert result.status_code == 200
        data = result.json()
        assert data["id"] == "_admin"
        assert data["type"] == "admin"
        assert data["name"] == admin_creds[0]

    def test_admin_id(self, admin_client: TestClient, admin_creds: tuple[str, str]):
        result = admin_client.get("/users/id/_admin")
        assert result.status_code == 200
        data = result.json()
        assert data["id"] == "_admin"
        assert data["type"] == "admin"
        assert data["name"] == admin_creds[0]

    def test_admin_name(self, admin_client: TestClient, admin_creds: tuple[str, str]):
        result = admin_client.get(f"/users/name/{admin_creds[0]}")
        assert result.status_code == 200
        data = result.json()
        assert data["id"] == "_admin"
        assert data["type"] == "admin"
        assert data["name"] == admin_creds[0]


@pytest.mark.user(username="basic", password="basic", groups=["general"])
@pytest.mark.user(username="moderator", password="admin", groups=["admins"])
@pytest.mark.group(name="general")
@pytest.mark.group(name="admins", display_name="Administrators")
@pytest.mark.parametrize(
    ["username", "password"], [("basic", "basic"), ("moderator", "admin")]
)
class TestUserQueries:

    def test_user_self(self, user_client, username, password):
        with user_client(username, password) as user_client:
            result = user_client.get("/users/self")
            assert result.status_code == 200
            data = result.json()
            assert data["type"] == "user"
            assert data["name"] == username

    def test_user_query(self, user_client, username, password):
        with user_client(username, password) as user_client:
            result = user_client.get(f"/users/name/{username}")
            assert result.status_code == 200
            data = result.json()
            assert data["type"] == "user"
            assert data["name"] == username

            result = user_client.get(f"/users/id/{data['id']}")
            assert result.status_code == 200
            data = result.json()
            assert data["type"] == "user"
            assert data["name"] == username


@pytest.mark.user(username="basic", password="basic")
@pytest.mark.user(username="moderator", password="admin")
class TestUsers:

    def test_user_list(
        self,
        admin_client: TestClient,
        admin_creds: tuple[str, str],
    ):
        result = admin_client.get("/users")
        assert result.status_code == 200
        data = result.json()
        assert type(data) == list
        assert len(data) == 3
        usernames = [i["name"] for i in data]
        for username in [admin_creds[0], "basic", "admin"]:
            assert username in usernames

    def test_user_create(self, admin_client: TestClient):
        result = admin_client.post(
            "/users/create", json={"username": "TEST_USER", "password": "TEST_PASSWORD"}
        )
        assert result.status_code == 201
        data = result.json()
        assert data["type"] == "user"
        assert data["name"] == "TEST_USER"
