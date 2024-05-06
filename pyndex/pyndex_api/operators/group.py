from functools import cached_property
from typing import Any
from unittest import result
from .base import BaseOperator, BaseOperatorModel
from ..util import BaseInstance, ApiError
from pyndex.common import AuthGroup


class GroupItem(AuthGroup, BaseOperatorModel["GroupOperator"]):
    def __init__(self, operator: "GroupOperator" = None, **data):
        super().__init__(**data)
        self._operator = operator


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
