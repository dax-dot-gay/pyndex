from typing import Any, Literal
from litestar import Controller, delete, get, post
from litestar.exceptions import *
from litestar.di import Provide
from pydantic import BaseModel, computed_field
from tinydb import where
from .user import guard_auth_enabled, RedactedAuth
from ..models.auth import (
    guard_admin,
    AuthGroup,
    AuthUser,
    AuthToken,
    PackagePermission,
    MetaPermission,
    PermissionSpecModel,
    AuthPermission,
)
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

    @get("/members")
    async def get_group_members(self, group: AuthGroup) -> list[RedactedAuth]:
        return [RedactedAuth.from_auth(i) for i in group.get_members()]

    @delete("/", guards=[guard_admin])
    async def delete_group(self, group: AuthGroup) -> None:
        group.delete()

    @post("/permissions")
    async def add_permission(
        self, auth: Any, group: AuthGroup, data: PermissionSpecModel
    ) -> list[PermissionSpecModel]:
        if data.permission in PackagePermission and not data.project:
            raise ValidationException(
                "Must specify `.project` if creating a package permission."
            )

        if data.permission in MetaPermission and data.project:
            raise ValidationException(
                "Cannot specify meta-permissions on specific projects."
            )

        if data.permission in MetaPermission and not auth.is_admin:
            raise NotAuthorizedException(
                "Cannot add meta-permissions without meta.admin access."
            )

        if data.permission in PackagePermission and auth.has_permission(
            PackagePermission.MANAGE, project=data.project
        ):
            raise NotAuthorizedException("Insufficient permissions to manage project")

        current_permissions = [
            i.permission for i in group.permissions(project=data.project)
        ]
        if data.permission in current_permissions:
            return [
                PermissionSpecModel(permission=i.permission, project=i.project)
                for i in group.permissions()
            ]

        created = AuthPermission(
            permission=data.permission,
            target_type="group",
            target_id=group.id,
            project=data.project,
        )
        created.save()
        return [
            PermissionSpecModel(permission=i.permission, project=i.project)
            for i in group.permissions()
        ]

    @get("/permissions")
    async def list_permissions(self, group: AuthGroup) -> list[PermissionSpecModel]:
        return [
            PermissionSpecModel(permission=i.permission, project=i.project)
            for i in group.permissions()
        ]

    @get("/permissions/{project:str}")
    async def get_project_permissions(
        self, group: AuthGroup, project: str
    ) -> list[PermissionSpecModel]:
        return [
            PermissionSpecModel(permission=i.permission, project=i.project)
            for i in group.permissions(project=project)
        ]
