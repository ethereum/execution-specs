"""Base class for all fixture loaders."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Self

from _pytest.nodes import Node


class Fixture(ABC):
    """
    Single fixture from a JSON file.

    It can be subclassed in combination with Item or Collector to create a
    fixture that can be collected by pytest.
    """

    test_file: str
    test_key: str
    test_dict: Dict[str, Any]

    def __init__(
        self,
        *args: Any,
        test_file: str,
        test_key: str,
        test_dict: Dict[str, Any],
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.test_file = test_file
        self.test_key = test_key
        self.test_dict = test_dict

    @classmethod
    def from_parent(
        cls,
        parent: Node,
        **kwargs: Any,
    ) -> Self:
        """Pytest hook that returns a fixture from a JSON file."""
        return super().from_parent(  # type: ignore[misc]
            parent=parent, **kwargs
        )

    @classmethod
    @abstractmethod
    def is_format(cls, test_dict: Dict[str, Any]) -> bool:
        """Return true if the object can be parsed as the fixture type."""
        pass
