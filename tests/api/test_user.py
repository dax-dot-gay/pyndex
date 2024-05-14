from typing import Callable, Iterator
import pytest
from pyndex.pyndex_api import Pyndex, UserItem

AS_USER = Callable[[str, str | None], Iterator[Pyndex]]


@pytest.mark.user(username="alice", password="alice", groups=["basic"])
@pytest.mark.user(
    username="bob", password="bob", groups=["basic"], server_permissions=["meta.create"]
)
@pytest.mark.user(username="linus", password="linus", groups=["admins"])
@pytest.mark.group(name="basic", display_name="Basic Group")
@pytest.mark.group(
    name="admins", display_name="Administrators", server_permissions=["meta.admin"]
)
class TestSelf:
    @pytest.mark.parametrize(
        ["username", "password"],
        [("alice", "alice"), ("bob", "bob"), ("linus", "linus")],
    )
    def test_password(self, username: str, password: str, as_user: AS_USER):
        with as_user(username, password) as _index:
            index: Pyndex = _index
            active = index.users.active
            assert active.current
            active.change_password(password, "TEST")
            assert active.instance.password == "TEST"
            active.change_password("TEST", password)
            assert active.instance.password == password

    @pytest.mark.parametrize(
        ["username", "password"],
        [("alice", "alice"), ("bob", "bob"), ("linus", "linus")],
    )
    def test_delete(self, username: str, password: str, as_user: AS_USER):
        with as_user(username, password) as _index:
            index: Pyndex = _index
            active = index.users.active
            assert active.current
            active.delete()
            try:
                index.users.all()
                assert False
            except:
                assert True


@pytest.mark.user(username="alice", password="alice", groups=["basic"])
@pytest.mark.user(
    username="bob", password="bob", groups=["basic"], server_permissions=["meta.create"]
)
@pytest.mark.user(username="linus", password="linus", groups=["admins"])
@pytest.mark.group(name="basic", display_name="Basic Group")
@pytest.mark.group(
    name="admins", display_name="Administrators", server_permissions=["meta.admin"]
)
@pytest.mark.package(dist="./dist/*", username="admin", password="admin")
@pytest.mark.parametrize(
    ["username"],
    [("alice",), ("bob",), ("linus",)],
)
class TestUsers:
    def test_query(self, username: str, as_admin: Pyndex):
        user = as_admin.users(username=username)
        assert user.name == username

    def test_all(self, as_admin: Pyndex, username: str):
        results = as_admin.users.all()
        assert len(results) == 4
        assert username in [i.name for i in results]

    def test_create(self, as_admin: Pyndex, username: str):
        result = as_admin.users.create(username + "_test", password=username)
        assert result.name == username + "_test"
        assert result.name in [i.name for i in as_admin.users.all()]

    def test_perm_manage(self, as_admin: Pyndex, username: str):
        results = as_admin.users(username=username).add_package_permission(
            "pkg.view", "pyndex"
        )
        assert "pkg.view" in [i.permission for i in results]
        results = as_admin.users(username=username).get_permissions(project="pyndex")
        assert "pkg.view" in [i.permission for i in results]
        results = as_admin.users(username=username).delete_package_permission(
            "pkg.view", "pyndex"
        )
        assert not "pkg.view" in [i.permission for i in results]
