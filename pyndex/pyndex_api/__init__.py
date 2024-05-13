from contextlib import contextmanager
from typing import Any, Generator

from httpx import Client
from .util import BaseInstance, ApiError
from .operators import *


class Pyndex(BaseInstance):
    @contextmanager
    def session(self, client: Client | None = None) -> Generator["Pyndex", Any, Any]:
        """Context manager to generate an active & connected session

        Yields:
            Pyndex: A reference to itself, now connected.
        """
        self.connect(client=client)
        yield self
        self.disconnect()

    @property
    def package(self) -> PackageOperator:
        return PackageOperator(self)

    @property
    def users(self) -> UserOperator:
        return UserOperator(self)

    @property
    def groups(self) -> GroupOperator:
        return GroupOperator(self)
