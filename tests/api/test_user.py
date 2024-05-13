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
@pytest.mark.parametrize(
    ["username"],
    [("alice",), ("bob",), ("linus",)],
)
class TestUsers:
    def test_query(self, username: str, as_admin: Pyndex):
        user = as_admin.users(username=username)
        assert user.name == username
