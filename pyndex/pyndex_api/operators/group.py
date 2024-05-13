from functools import cached_property
from typing import Any
from unittest import result
from .base import BaseOperator, BaseOperatorModel
from ..util import BaseInstance, ApiError
from pyndex.common import (
    AuthGroup,
    PermissionSpecModel,
    MetaPermission,
    PackagePermission,
)
from .user import UserItem


class GroupItem(AuthGroup, BaseOperatorModel["GroupOperator"]):
    def __init__(self, operator: "GroupOperator" = None, **data):
        super().__init__(**data)
        self._operator = operator

    def add_member(self, member: UserItem) -> None:
        """Adds a member from a UserItem.

        Args:
            member (UserItem): Member to add

        Raises:
            ApiError.from_response: Raised if adding the member fails
        """
        result = self.client.post(
            self.url("groups", "id", self.id, "members"),
            params={"auth_type": "user", "auth_id": member.id},
        )
        if not result.is_success:
            raise ApiError.from_response(result)

    def delete_member(self, member: UserItem) -> None:
        """Removes a member from a group

        Args:
            member (UserItem): Member to remove

        Raises:
            ApiError.from_response: Raised if removing the member fails
        """
        result = self.client.delete(
            self.url("groups", "id", self.id, "members"),
            params={"auth_type": "user", "auth_id": member.id},
        )
        if not result.is_success:
            raise ApiError.from_response(result)

    def get_members(self) -> list[UserItem]:
        """Gets a list of a group's members.

        Raises:
            ApiError.from_response: Raised if getting group members fails

        Returns:
            list[UserItem]: List of UserItems that are members of the group
        """
        result = self.client.get(self.url("groups", "id", self.id, "members"))
        if not result.is_success:
            raise ApiError.from_response(result)
        return [UserItem(operator=self.instance.users, **i) for i in result.json()]

    def delete(self) -> None:
        """Deletes the group

        Raises:
            ApiError.from_response: Raised if deletion fails
        """
        result = self.client.delete(self.url("groups", "id", self.id))
        if not result.is_success:
            raise ApiError.from_response(result)

    def add_permission(self, spec: PermissionSpecModel) -> list[PermissionSpecModel]:
        """Adds a permission to the group

        Args:
            spec (PermissionSpecModel): Permission specification model

        Raises:
            ApiError.from_response: Raised if adding the permission fails

        Returns:
            list[PermissionSpecModel]: List of permissions held by this group
        """
        result = self.client.post(
            self.url("groups", "id", self.id, "permissions"),
            json=spec.model_dump(mode="json"),
        )
        if result.is_success:
            return [PermissionSpecModel(**i) for i in result.json()]
        raise ApiError.from_response(result)

    def add_server_permission(
        self, permission: MetaPermission
    ) -> list[PermissionSpecModel]:
        """Utility function to add a server permission in a simple way"""
        return self.add_permission(PermissionSpecModel(permission=permission))

    def add_package_permission(
        self, permission: PackagePermission, package: str
    ) -> list[PermissionSpecModel]:
        """Utility function to add a package permission in a simple way"""
        return self.add_permission(
            PermissionSpecModel(permission=permission, project=package)
        )

    def get_permissions(self, project: str | None = None) -> list[PermissionSpecModel]:
        """Gets all of a group's permissions, optionally associated with a specific project

        Args:
            project (str | None, optional): Project name. Defaults to None.

        Raises:
            ApiError.from_response: Raised if returning permissions fails

        Returns:
            list[PermissionSpecModel]: List of permissions. If `project` is specified, only permissions associated with that project will be returned.
        """
        if project:
            result = self.client.get(
                self.url("groups", "id", self.id, "permissions", project)
            )
        else:
            result = self.client.get(self.url("groups", "id", self.id, "permissions"))
        if result.is_success:
            return [PermissionSpecModel(**i) for i in result.json()]
        raise ApiError.from_response(result)

    def delete_permission(self, spec: PermissionSpecModel) -> list[PermissionSpecModel]:
        """Deletes a permission based on a specification model

        Args:
            spec (PermissionSpecModel): Permission query specification

        Raises:
            ApiError.from_response: Raised if removing permission fails

        Returns:
            list[PermissionSpecModel]: Returns new list of permissions
        """
        result = self.client.post(
            self.url("groups", "id", self.id, "permissions", "delete"),
            json=spec.model_dump(mode="json"),
        )
        if result.is_success:
            return [PermissionSpecModel(**i) for i in result.json()]
        raise ApiError.from_response(result)

    def delete_server_permission(
        self, permission: MetaPermission
    ) -> list[PermissionSpecModel]:
        """Utility function to delete server permissions"""
        return self.delete_permission(PermissionSpecModel(permission=permission))

    def delete_package_permission(
        self, permission: PackagePermission, package: str
    ) -> list[PermissionSpecModel]:
        """Utility function to delete package permissions"""
        return self.delete_permission(
            PermissionSpecModel(permission=permission, project=package)
        )


class GroupOperator(BaseOperator):
    def __call__(
        self, group_id: str | None = None, group_name: str | None = None
    ) -> GroupItem | None:
        """Returns a GroupItem based on ID or name

        Args:
            group_id (str | None, optional): Group ID (must not specify name). Defaults to None.
            group_name (str | None, optional): Group name (must not specify ID). Defaults to None.

        Raises:
            ValueError: Raised if arguments are provided incorrectly

        Returns:
            GroupItem | None: GroupItem if found, otherwise None
        """
        if group_id == None and group_name == None:
            raise ValueError("Exactly one of group_id or group_name is required.")
        if group_id != None and group_name != None:
            raise ValueError("Exactly one of group_id or group_name is required.")

        if group_id:
            result = self.client.get(self.url("groups", "id", group_id))
            if result.is_success:
                return GroupItem(operator=self, **result.json())
            return None
        else:
            result = self.client.get(self.url("groups", "name", group_name))
            if result.is_success:
                return GroupItem(operator=self, **result.json())
            return None

    def create(self, name: str, display_name: str | None = None) -> GroupItem:
        """Creates a new group

        Args:
            name (str): Group name (must be unique)
            display_name (str | None, optional): Human-friendly name, if desired. Defaults to None.

        Raises:
            ApiError.from_response: Raised if group creation fails

        Returns:
            GroupItem: Created GroupItem
        """
        result = self.client.post(
            self.url("groups", "create"),
            json={"name": name, "display_name": display_name},
        )
        if result.is_success:
            return GroupItem(operator=self, **result.json())
        raise ApiError.from_response(result)

    def all(self) -> list[GroupItem]:
        """Returns a list of all groups

        Raises:
            ApiError.from_response: Raised if listing fails

        Returns:
            list[GroupItem]: List of all GroupItems
        """
        result = self.client.get(self.url("groups"))
        if result.is_success:
            return [GroupItem(operator=self, **i) for i in result.json()]
        raise ApiError.from_response(result)
