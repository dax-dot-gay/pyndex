from functools import cached_property
from typing import Any
from .base import BaseOperator, BaseOperatorModel
from ..util import BaseInstance, ApiError
from pyndex.common import RedactedAuth


class UserItem(RedactedAuth, BaseOperatorModel["UserOperator"]):
    def __init__(self, operator: "UserOperator" = None, **data):
        super().__init__(**data)
        self._operator = operator


class UserOperator(BaseOperator):
    def __call__(
        self, username: str | None = None, user_id: str | None = None
    ) -> UserItem | None:
        """Fetches an individual user based on username OR user ID

        Args:
            username (str | None, optional): Username to find. Defaults to None.
            user_id (str | None, optional): User ID to find. Defaults to None.

        Raises:
            ValueError: If none or both of Username or User ID are specified

        Returns:
            UserItem | None: Resulting user or None if not found
        """
        if not username and not user_id:
            raise ValueError("Must specify username or user ID")
        if username and user_id:
            raise ValueError("Cannot specify both username & user ID")

        if username:
            result = self.client.get(self.url("users", "name", username))
        else:
            result = self.client.get(self.url("users", "id", user_id))

        if result.is_success:
            return UserItem(operator=self, **result.json())
        return None

    def all(self) -> list[UserItem]:
        """Returns a list of all users

        Raises:
            ApiError.from_response: If the API request fails

        Returns:
            list[UserItem]: List of Users
        """
        result = self.client.get(self.url("users"))
        if result.is_success:
            return [UserItem(operator=self, **i) for i in result.json()]
        raise ApiError.from_response(result)

    @cached_property
    def active(self) -> UserItem:
        """Returns the active user

        Raises:
            ApiError.from_response: Raised if the user is not logged in or the current user is otherwise inaccessible

        Returns:
            UserItem: Current user
        """
        result = self.client.get(self.url("users", "self"))
        if result.is_success:
            return UserItem(operator=self, **result.json())

        raise ApiError.from_response(result)

    def create(self, username: str, password: str | None = None) -> UserItem:
        """Creates a new user given a username and optional password. This method requires the logged-in user to have the meta.admin permission.

        Args:
            username (str): Username (unique)
            password (str | None): Optional password. Defaults to None.

        Raises:
            ApiError.from_response: Raised if user creation fails (ie if the current user has insufficient permissions)

        Returns:
            UserItem: Created User
        """
        result = self.client.post(
            self.url("users", "create"),
            json={"username": username, "password": password},
        )
        if result.is_success:
            return UserItem(operator=self, **result.json())
        raise ApiError.from_response(result)
