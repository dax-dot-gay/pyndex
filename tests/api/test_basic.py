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
class TestBasic:
    @pytest.mark.parametrize(
        ["username", "password"],
        [("alice", "alice"), ("bob", "bob"), ("linus", "linus")],
    )
    def test_login(
        self,
        username: str,
        password: str,
        as_user: AS_USER,
    ):
        with as_user(username, password) as _index:
            index: Pyndex = _index
            active = index.users.active
            assert isinstance(active, UserItem)
            assert active.current
            assert active.name == username

    @pytest.mark.parametrize(
        ["username", "password", "groups"],
        [
            ("alice", "alice", ["basic"]),
            ("bob", "bob", ["basic"]),
            ("linus", "linus", ["admins"]),
        ],
    )
    def test_groups(
        self, username: str, password: str, groups: list[str], as_user: AS_USER
    ):
        with as_user(username, password) as _index:
            index: Pyndex = _index
            active = index.users.active
            assert len(active.groups) == len(groups)
            assert all([i.name in groups for i in active.groups])

    @pytest.mark.parametrize(
        ["username", "password", "permissions"],
        [
            ("alice", "alice", []),
            ("bob", "bob", ["meta.create"]),
            ("linus", "linus", ["meta.admin"]),
        ],
    )
    def test_permissions(
        self, username: str, password: str, permissions: list[str], as_user: AS_USER
    ):
        with as_user(username, password) as _index:
            index: Pyndex = _index
            active = index.users.active
            perms = active.get_permissions()
            assert len(perms) == len(permissions)
            assert all([i.permission in permissions for i in perms])
