"""Base class for all fixture loaders."""

import json
from abc import ABC, abstractmethod
from functools import cached_property
from typing import Any, Dict, Generator, List, Self, Type

from _pytest.nodes import Node
from pytest import Collector, Config, File, Item


class FixtureTestItem(Item):
    """
    Test item that comes from a fixture file.
    """

    @property
    def fixtures_file(self) -> "FixturesFile":
        """Return the fixtures file from which the test was extracted."""
        raise NotImplementedError()


class Fixture(ABC):
    """
    Single fixture from a JSON file.

    It can be subclassed in combination with Item or Collector to create a
    fixture that can be collected by pytest.
    """

    test_file: str
    test_key: str

    def __init__(
        self,
        *args: Any,
        test_file: str,
        test_key: str,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.test_file = test_file
        self.test_key = test_key

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

    @classmethod
    @abstractmethod
    def has_desired_fork(
        cls, test_dict: Dict[str, Any], config: Config
    ) -> bool:
        """
        Check if the fork(s) relevant to this item/
        collector are in the desired forks list.
        """
        pass


ALL_FIXTURE_TYPES: List[Type[Fixture]] = []


class FixturesFile(File):
    """Single JSON file containing fixtures."""

    @cached_property
    def data(self) -> Dict[str, Any]:
        """Return the JSON data of the full file."""
        # loaded once per worker per file (thanks to cached_property)
        with self.fspath.open("r", encoding="utf-8") as f:
            return json.load(f)

    def clear_data_cache(self) -> None:
        """Drop the data cache."""
        if hasattr(self, "data"):
            del self.data

    def collect(
        self: Self,
    ) -> Generator[Item | Collector, None, None]:
        """Collect test cases from a single JSON fixtures file."""
        try:
            loaded_file = self.data
        except Exception:
            return  # Skip *.json files that are unreadable.
        if isinstance(loaded_file, dict):
            for key, test_dict in loaded_file.items():
                if not isinstance(test_dict, dict):
                    continue
                for fixture_type in ALL_FIXTURE_TYPES:
                    if not fixture_type.is_format(test_dict):
                        continue
                    # Check if we should collect this test
                    if not fixture_type.has_desired_fork(
                        test_dict, self.config
                    ):
                        continue
                    yield fixture_type.from_parent(  # type: ignore
                        parent=self,
                        name=key,
                        test_file=str(self.path),
                        test_key=key,
                    )
        # Make sure we don't keep anything from collection in memory.
        self.clear_data_cache()
