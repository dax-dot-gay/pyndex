from litestar.testing import TestClient


class TestUsers:
    def test_admin(self, admin_client: TestClient):
        result = admin_client.get("/users/self")
        assert result.status_code == 200
