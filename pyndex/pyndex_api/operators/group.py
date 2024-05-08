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
        result = self.client.post(
            self.url("groups", "id", self.id, "members"),
            params={"auth_type": "user", "auth_id": member.id},
        )
        if not result.is_success:
            raise ApiError.from_response(result)

    def delete_member(self, member: UserItem) -> None:
        result = self.client.delete(
            self.url("groups", "id", self.id, "members"),
            params={"auth_type": "user", "auth_id": member.id},
        )
        if not result.is_success:
            raise ApiError.from_response(result)

    def get_members(self) -> list[UserItem]:
        result = self.client.get(self.url("groups", "id", self.id, "members"))
        if not result.is_success:
            raise ApiError.from_response(result)
        return [UserItem(operator=self.instance.users, **i) for i in result.json()]

    def delete(self) -> None:
        result = self.client.delete(self.url("groups", "id", self.id))
        if not result.is_success:
            raise ApiError.from_response(result)

    def add_permission(self, spec: PermissionSpecModel) -> list[PermissionSpecModel]:
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
        return self.add_permission(PermissionSpecModel(permission=permission))

    def add_package_permission(
        self, permission: PackagePermission, package: str
    ) -> list[PermissionSpecModel]:
        return self.add_permission(
            PermissionSpecModel(permission=permission, project=package)
        )

    def get_permissions(self, project: str | None = None) -> list[PermissionSpecModel]:
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
        return self.delete_permission(PermissionSpecModel(permission=permission))

    def delete_package_permission(
        self, permission: PackagePermission, package: str
    ) -> list[PermissionSpecModel]:
        return self.delete_permission(
            PermissionSpecModel(permission=permission, project=package)
        )


class GroupOperator(BaseOperator):
    def __call__(
        self, group_id: str | None = None, group_name: str | None = None
    ) -> GroupItem | None:
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
        result = self.client.post(
            self.url("groups", "create"),
            json={"name": name, "display_name": display_name},
        )
        if result.is_success:
            return GroupItem(operator=self, **result.json())
        raise ApiError.from_response(result)

    def all(self) -> list[GroupItem]:
        result = self.client.get(self.url("groups"))
        if result.is_success:
            return [GroupItem(operator=self, **i) for i in result.json()]
        raise ApiError.from_response(result)
