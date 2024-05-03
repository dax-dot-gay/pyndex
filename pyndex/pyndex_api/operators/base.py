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
    def client(self) -> Client | None:
        """Returns a reference to the parent instance's Client

        Returns:
            Client | None: Client object, or None if not connected.
        """
        if self.instance.client and not self.instance.client.is_closed:
            return self.instance.client
        return None

    def url(self, *parts: str) -> str:
        """Convenience wrapper around parent instance's url() function

        Returns:
            str: Concatenated URL
        """
        return self.instance.url(*parts)
