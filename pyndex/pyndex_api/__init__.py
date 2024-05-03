from contextlib import contextmanager
from typing import Any, Generator
from .util import BaseInstance
from .operators import *


class Pyndex(BaseInstance):
    @contextmanager
    def session(self) -> Generator["Pyndex", Any, Any]:
        """Context manager to generate an active & connected session

        Yields:
            Pyndex: A reference to itself, now connected.
        """
        self.connect()
        yield self
        self.disconnect()

    @property
    def package(self) -> PackageOperator:
        return PackageOperator(self)

    @property
    def users(self) -> UserOperator:
        return UserOperator(self)
