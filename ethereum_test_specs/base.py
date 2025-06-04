"""Base test class and helper functions for Ethereum state and blockchain tests."""

from abc import abstractmethod
from functools import reduce
from os import path
from pathlib import Path
from typing import Callable, ClassVar, Dict, Generator, List, Sequence, Type, TypeVar

import pytest
from pydantic import BaseModel, Field, PrivateAttr

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


T = TypeVar("T", bound="BaseTest")


class BaseTest(BaseModel):
    """Represents a base Ethereum test which must return a single test fixture."""

    tag: str = ""

    _request: pytest.FixtureRequest | None = PrivateAttr(None)

    spec_types: ClassVar[Dict[str, Type["BaseTest"]]] = {}

    # Transition tool specific fields
    t8n_dump_dir: Path | None = Field(None, exclude=True)
    t8n_call_counter: int = Field(0, exclude=True)

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
    def __pydantic_init_subclass__(cls, **kwargs):
        """
        Register all subclasses of BaseFixture with a fixture format name set
        as possible fixture formats.
        """
        if cls.pytest_parameter_name():
            # Register the new fixture format
            BaseTest.spec_types[cls.pytest_parameter_name()] = cls

    @classmethod
    def from_test(
        cls: Type[T],
        *,
        base_test: "BaseTest",
        **kwargs,
    ) -> T:
        """Create a test in a different format from a base test."""
        new_instance = cls(
            tag=base_test.tag,
            t8n_dump_dir=base_test.t8n_dump_dir,
            **kwargs,
        )
        new_instance._request = base_test._request
        return new_instance

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
        t8n: TransitionTool,
        fork: Fork,
        fixture_format: FixtureFormat,
    ) -> BaseFixture:
        """Generate the list of test fixtures."""
        pass

    def execute(
        self,
        *,
        fork: Fork,
        execute_format: ExecuteFormat,
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
        if cls == BaseTest:
            return ""
        return reduce(lambda x, y: x + ("_" if y.isupper() else "") + y, cls.__name__).lower()

    def get_next_transition_tool_output_path(self) -> str:
        """Return path to the next transition tool output file."""
        if not self.t8n_dump_dir:
            return ""
        current_value = self.t8n_call_counter
        self.t8n_call_counter += 1
        return path.join(
            self.t8n_dump_dir,
            str(current_value),
        )

    def is_tx_gas_heavy_test(self) -> bool:
        """Check if the test is gas-heavy for transaction execution."""
        if self._request is not None and hasattr(self._request, "node"):
            node = self._request.node
            has_slow_marker = node.get_closest_marker("slow") is not None
            has_zkevm_marker = node.get_closest_marker("zkevm") is not None
            return has_slow_marker or has_zkevm_marker
        return False

    def is_exception_test(self) -> bool | None:
        """
        Check if the test is an exception test (invalid block, invalid transaction).

        `None` is returned if it's not possible to determine if the test is negative or not.
        This is the case when the test is not run in pytest.
        """
        if self._request is not None and hasattr(self._request, "node"):
            return self._request.node.get_closest_marker("exception_test") is not None
        return None

    def node_id(self) -> str:
        """Return the node ID of the test."""
        if self._request is not None and hasattr(self._request, "node"):
            return self._request.node.nodeid
        return ""

    def check_exception_test(
        self,
        *,
        exception: bool,
    ):
        """Compare the test marker against the outcome of the test."""
        negative_test_marker = self.is_exception_test()
        if negative_test_marker is None:
            return
        if negative_test_marker != exception:
            if exception:
                raise Exception(
                    "Test produced an invalid block or transaction but was not marked with the "
                    "`exception_test` marker. Add the `@pytest.mark.exception_test` decorator "
                    "to the test."
                )
            else:
                raise Exception(
                    "Test didn't produce an invalid block or transaction but was marked with the "
                    "`exception_test` marker. Remove the `@pytest.mark.exception_test` decorator "
                    "from the test."
                )


TestSpec = Callable[[Fork], Generator[BaseTest, None, None]]
