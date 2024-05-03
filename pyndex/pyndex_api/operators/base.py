from typing import TypeVar
from pydantic import BaseModel
from ..util import BaseInstance
from httpx import Client


class BaseOperator:
    def __init__(self, instance: BaseInstance):
        """Initialize a basic Operator with the current instance

        Args:
            instance (BaseInstance): The current instance (Actually Pyndex, but BaseIndex is used here for typing convenience.)
        """
        self.instance = instance

    @property
    def client(self) -> Client:
        """Returns a reference to the parent instance's Client. If the client isn't connected, raises a RuntimeError

        Returns:
            Client: Client object
        """
        if self.instance.client and not self.instance.client.is_closed:
            return self.instance.client
        raise RuntimeError("Client is disconnected.")

    def url(self, *parts: str) -> str:
        """Convenience wrapper around parent instance's url() function

        Returns:
            str: Concatenated URL
        """
        return self.instance.url(*parts)


TOperator = TypeVar("TOperator", bound=BaseOperator)


class BaseOperatorModel[TOperator]:
    def __init__(self, operator: TOperator = None):
        self._operator = operator

    @property
    def operator(self) -> TOperator:
        return self._operator

    @property
    def instance(self) -> BaseInstance:
        return self._operator.instance

    @property
    def client(self) -> Client:
        return self._operator.client

    def url(self, *parts) -> str:
        return self._operator.url(*parts)
