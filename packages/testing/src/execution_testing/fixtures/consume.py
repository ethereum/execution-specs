"""Defines models for index files and consume test cases."""

import datetime
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, List, Optional, TextIO

from pydantic import BaseModel, RootModel

from execution_testing.base_types import HexNumber
from execution_testing.forks import Fork

from .base import BaseFixture, FixtureFormat
from .file import Fixtures


class FixtureConsumer(ABC):
    """Abstract class for verifying Ethereum test fixtures."""

    fixture_formats: List[FixtureFormat]

    def can_consume(
        self,
        fixture_format: FixtureFormat,
    ) -> bool:
        """Return whether the fixture format is consumable by this consumer."""
        return fixture_format in self.fixture_formats

    @abstractmethod
    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: str | None = None,
        debug_output_path: Path | None = None,
    ) -> None:
        """
        Test the client with the specified fixture using its direct consumer
        interface.
        """
        raise NotImplementedError(
            "The `consume_fixture()` function is not supported by this tool."
        )


class TestCaseBase(BaseModel):
    """Base model for a test case used in EEST consume commands."""

    id: str
    fixture_hash: HexNumber | None = None
    fork: Fork | None = None
    format: FixtureFormat
    pre_hash: str | None = None
    __test__ = False  # stop pytest from collecting this class as a test


class TestCaseStream(TestCaseBase):
    """The test case model used to load test cases from a stream (stdin)."""

    fixture: BaseFixture
    __test__ = False  # stop pytest from collecting this class as a test


class TestCaseIndexFile(TestCaseBase):
    """
    The test case model used to save/load test cases to/from an index file.
    """

    json_path: Path
    __test__ = False  # stop pytest from collecting this class as a test

    # TODO: add pytest marks
    """
    ConsumerTypes = Literal["all", "direct", "rlp", "engine"]
    @classmethod
    def _marks_default(cls):
        return {consumer_type: [] for consumer_type in get_args(ConsumerTypes)}
    marks: Mapping[ConsumerTypes, List[pytest.MarkDecorator]] = field(
        default_factory=lambda: TestCase._marks_default()
    )
    """


class IndexFile(BaseModel):
    """The model definition used for fixture index files."""

    root_hash: HexNumber | None
    created_at: datetime.datetime
    test_count: int
    forks: Optional[List[Fork]] = []
    fixture_formats: Optional[List[str]] = []
    test_cases: List[TestCaseIndexFile]


class TestCases(RootModel):
    """Root model defining a list test cases used in consume commands."""

    root: List[TestCaseIndexFile] | List[TestCaseStream]
    __test__ = False  # stop pytest from collecting this class as a test

    def __len__(self) -> int:
        """Return the number of test cases in the root list."""
        return len(self.root)

    def __getitem__(self, position: int) -> TestCaseIndexFile | TestCaseStream:
        """Retrieve a test case by its index."""
        return self.root[position]

    def __setitem__(
        self, position: int, value: TestCaseIndexFile | TestCaseStream
    ) -> None:
        """Set a test case at a particular index."""
        self.root[position] = value  # type: ignore

    def __delitem__(self, position: int) -> None:
        """Remove a test case at a particular index."""
        del self.root[position]

    def append(self, item: TestCaseIndexFile | TestCaseStream) -> None:
        """Append a test case to the root list."""
        self.root.append(item)  # type: ignore

    def insert(
        self, position: int, value: TestCaseIndexFile | TestCaseStream
    ) -> None:
        """Insert a test case at a given position."""
        self.root.insert(position, value)  # type: ignore

    def remove(self, value: TestCaseIndexFile | TestCaseStream) -> None:
        """Remove a test case from the root list."""
        self.root.remove(value)  # type: ignore

    def pop(self, position: int = -1) -> TestCaseIndexFile | TestCaseStream:
        """Remove and return a test case at the given position."""
        return self.root.pop(position)

    def clear(self) -> None:
        """Remove all items from the root list."""
        self.root.clear()

    def __iter__(self) -> Iterator[TestCaseIndexFile | TestCaseStream]:  # type: ignore [override]
        """Return an iterator for the root list."""
        return iter(self.root)

    def __repr__(self) -> str:
        """Return a string representation of the TestCases object."""
        return f"{self.__class__.__name__}(root={self.root})"

    @classmethod
    def from_stream(cls, fd: TextIO) -> "TestCases":
        """Create a TestCases object from a stream."""
        fixtures: Fixtures = Fixtures.model_validate_json(fd.read())
        test_cases = [
            TestCaseStream(
                id=fixture_name,
                fixture_hash=fixture.hash,
                fork=fixture.get_fork(),
                format=fixture.__class__,
                fixture=fixture,
            )
            for fixture_name, fixture in fixtures.items()
        ]
        return cls(root=test_cases)

    @classmethod
    def from_index_file(cls, index_file: Path) -> "TestCases":
        """Create a TestCases object from an index file."""
        index: IndexFile = IndexFile.model_validate_json(
            index_file.read_text()
        )
        return cls(root=index.test_cases)
