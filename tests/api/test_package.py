from typing import Callable, Iterator
import pytest
from pyndex.pyndex_api import Pyndex, UserItem

AS_USER = Callable[[str, str | None], Iterator[Pyndex]]


@pytest.mark.package(dist="./dist/*", username="admin", password="admin")
@pytest.mark.user(username="alice", password="alice")
@pytest.mark.user(username="bob", password="bob")
@pytest.mark.user(username="linus", password="linus", groups=["admins"])
@pytest.mark.group(
    name="admins", display_name="Administrators", server_permissions=["meta.admin"]
)
class TestPackageFormat:
    def test_access_control(self, as_user: AS_USER, as_admin: Pyndex):
        successful = as_admin.package("pyndex")
        assert successful != None
        assert successful.info.name == "pyndex"

        with as_user("alice", password="alice") as index:
            unsuccessful = index.package("pyndex")
            assert unsuccessful == None
            as_admin.users(username="alice").add_package_permission(
                "pkg.view", "pyndex"
            )

        with as_user("linus", password="linus") as index:
            successful2 = index.package("pyndex")
            assert successful2 != None
            assert successful2.info.name == "pyndex"

        with as_user("alice", password="alice") as index:
            successful3 = index.package("pyndex")
            assert successful3 != None
            assert successful3.info.name == "pyndex"
