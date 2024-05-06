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


@pytest.mark.parametrize("username", ["basic", "moderator", "project_owner"])
class TestUserQueries:
    def test_user_self(self, dynamic_user, username):
        with dynamic_user(username) as user_client:
            result = user_client.get("/users/self")
            assert result.status_code == 200
            data = result.json()
            assert data["type"] == "user"
            assert data["name"] == username

    def test_user_query(self, dynamic_user, username):
        with dynamic_user(username) as user_client:
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
