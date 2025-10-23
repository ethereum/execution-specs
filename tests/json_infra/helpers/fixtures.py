"""Base class for all fixture loaders."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Self, Type

from _pytest.nodes import Node
from pytest import Collector, File, Item


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


ALL_FIXTURE_TYPES: List[Type[Fixture]] = []


class FixturesFile(File):
    """Single JSON file containing fixtures."""

    def collect(
        self: Self,
    ) -> Generator[Item | Collector, None, None]:
        """Collect test cases from a single JSON fixtures file."""
        with open(self.path, "r") as file:
            try:
                loaded_file = json.load(file)
            except Exception:
                return  # Skip *.json files that are unreadable.
            if not isinstance(loaded_file, dict):
                return
            for key, test_dict in loaded_file.items():
                if not isinstance(test_dict, dict):
                    continue
                for fixture_type in ALL_FIXTURE_TYPES:
                    if not fixture_type.is_format(test_dict):
                        continue
                    name = key
                    if "::" in name:
                        name = name.split("::")[1]
                    yield fixture_type.from_parent(  # type: ignore
                        parent=self,
                        name=name,
                        test_file=str(self.path),
                        test_key=key,
                        test_dict=test_dict,
                    )
