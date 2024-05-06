from typing import Literal
from litestar import Controller, get, post
from litestar.exceptions import *
from litestar.di import Provide
from pydantic import BaseModel, computed_field
from tinydb import where
from .user import guard_auth_enabled, RedactedAuth
from ..models.auth import guard_admin, AuthGroup, AuthUser, AuthToken
from ..context import Context


class GroupCreationModel(BaseModel):
    name: str
    display_name: str | None = None

    @computed_field
    @property
    def display(self) -> str:
        if self.display_name:
            return self.display_name
        return self.name


class GroupController(Controller):
    """Operations pertaining to non-specific groups"""

    path = "/groups"
    guards = [guard_auth_enabled]

    @post("/create", guards=[guard_admin])
    async def create_group(self, data: GroupCreationModel) -> AuthGroup:
        """Creates a group.

        Args:
            data (GroupCreationModel): Group name & optional display name

        Raises:
            MethodNotAllowedException: Raised if a group with the requested name already exists.

        Returns:
            AuthGroup: Created group
        """
        if AuthGroup.exists(where("name") == data.name):
            raise MethodNotAllowedException("Group already exists")

        created = AuthGroup(name=data.name, display_name=data.display_name)
        created.save()
        return created

    @get("/")
    async def list_groups(self) -> list[AuthGroup]:
        """Returns a list of all existing groups

        Returns:
            list[AuthGroup]: Group list
        """
        return AuthGroup.all()


async def provide_group(method: Literal["id", "name"], value: str) -> AuthGroup:
    """Retrieves a group with a group ID or group name

    Args:
        method (Literal["id", "name"]): Query method
        value (str): ID or name

    Returns:
        AuthGroup: Retrieved group
    """
    if not method in ["id", "name"]:
        raise ValidationException(f"Unknown query method {method}")

    if method == "id":
        result = AuthGroup.get(value)
        if not result:
            raise NotFoundException("Unknown group ID")
        return result
    else:
        result = AuthGroup.find_one(where("name") == value)
        if not result:
            raise NotFoundException("Unknown group name")
        return result


class SpecificGroupController(Controller):
    """Operations pertaining to a single existing group"""

    path = "/groups/{method:str}/{value:str}"
    guards = [guard_auth_enabled]
    dependencies = {"group": Provide(provide_group)}

    @get("/")
    async def get_group(self, group: AuthGroup) -> AuthGroup:
        return group

    @post("/members", guards=[guard_admin])
    async def add_member(
        self,
        group: AuthGroup,
        auth_type: Literal["user", "token"],
        auth_id: str | None = None,
    ) -> list[RedactedAuth]:
        match auth_type:
            case "user":
                if not auth_id:
                    raise ValidationException("Query parameter `auth_id` is required.")
                auth = AuthUser.get(auth_id)
                if not auth:
                    raise NotFoundException(f"User with id `{auth_id}` not found.")

            case "token":
                if not auth_id:
                    raise ValidationException("Query parameter `auth_id` is required.")
                auth = AuthToken.get(auth_id)
                if not auth:
                    raise NotFoundException(f"Token with id `{auth_id}` not found.")

        if not group.id in auth.groups:
            auth.groups.append(group.id)

        auth.save()
        return [RedactedAuth.from_auth(i) for i in group.get_members()]
