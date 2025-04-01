"""Base test class and helper functions for Ethereum state and blockchain tests."""

from abc import abstractmethod
from functools import reduce
from itertools import count
from os import path
from pathlib import Path
from typing import Callable, ClassVar, Dict, Generator, Iterator, List, Optional, Sequence

import pytest
from pydantic import BaseModel, Field

from ethereum_clis import Result, TransitionTool
from ethereum_test_base_types import to_hex
from ethereum_test_execution import BaseExecute, ExecuteFormat, LabeledExecuteFormat
from ethereum_test_fixtures import BaseFixture, FixtureFormat, LabeledFixtureFormat
from ethereum_test_forks import Fork
from ethereum_test_types import Environment, Withdrawal


class HashMismatchExceptionError(Exception):
    """Exception raised when the expected and actual hashes don't match."""

    def __init__(self, expected_hash, actual_hash, message="Hashes do not match"):
        """Initialize the exception with the expected and actual hashes."""
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        """Return the error message."""
        return f"{self.message}: Expected {self.expected_hash}, got {self.actual_hash}"


def verify_result(result: Result, env: Environment):
    """
    Verify that values in the t8n result match the expected values.
    Raises exception on unexpected values.
    """
    if env.withdrawals is not None:
        assert result.withdrawals_root == to_hex(Withdrawal.list_root(env.withdrawals))


class BaseTest(BaseModel):
    """Represents a base Ethereum test which must return a single test fixture."""

    tag: str = ""

    # Transition tool specific fields
    t8n_dump_dir: Path | None = Field(None, exclude=True)
    _t8n_call_counter: Iterator[int] = count(0)

    supported_fixture_formats: ClassVar[Sequence[FixtureFormat | LabeledFixtureFormat]] = []
    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = []

    supported_markers: ClassVar[Dict[str, str]] = {}

    @classmethod
    def discard_fixture_format_by_marks(
        cls,
        fixture_format: FixtureFormat,
        fork: Fork,
        markers: List[pytest.Mark],
    ) -> bool:
        """Discard a fixture format from filling if the appropriate marker is used."""
        return False

    @classmethod
    def discard_execute_format_by_marks(
        cls,
        execute_format: ExecuteFormat,
        fork: Fork,
        markers: List[pytest.Mark],
    ) -> bool:
        """Discard an execute format from executing if the appropriate marker is used."""
        return False

    @abstractmethod
    def generate(
        self,
        *,
        request: pytest.FixtureRequest,
        t8n: TransitionTool,
        fork: Fork,
        fixture_format: FixtureFormat,
        eips: Optional[List[int]] = None,
    ) -> BaseFixture:
        """Generate the list of test fixtures."""
        pass

    def execute(
        self,
        *,
        fork: Fork,
        execute_format: ExecuteFormat,
        eips: Optional[List[int]] = None,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        raise Exception(f"Unsupported execute format: {execute_format}")

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Must return the name of the parameter used in pytest to select this
        spec type as filler for the test.

        By default, it returns the underscore separated name of the class.
        """
        return reduce(lambda x, y: x + ("_" if y.isupper() else "") + y, cls.__name__).lower()

    def get_next_transition_tool_output_path(self) -> str:
        """Return path to the next transition tool output file."""
        if not self.t8n_dump_dir:
            return ""
        return path.join(
            self.t8n_dump_dir,
            str(next(self._t8n_call_counter)),
        )


TestSpec = Callable[[Fork], Generator[BaseTest, None, None]]
