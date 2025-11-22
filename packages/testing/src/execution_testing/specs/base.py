"""
Base test class and helper functions for Ethereum state and blockchain tests.
"""

import hashlib
from abc import abstractmethod
from enum import StrEnum, unique
from functools import reduce
from os import path
from pathlib import Path
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Sequence,
    Type,
)

import pytest
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from typing_extensions import Self

from execution_testing.base_types import to_hex
from execution_testing.client_clis import Result, TransitionTool
from execution_testing.client_clis.cli_types import OpcodeCount
from execution_testing.execution import (
    BaseExecute,
    ExecuteFormat,
    LabeledExecuteFormat,
)
from execution_testing.fixtures import (
    BaseFixture,
    FixtureFormat,
    LabeledFixtureFormat,
    PreAllocGroupBuilders,
)
from execution_testing.forks import Fork
from execution_testing.forks.base_fork import BaseFork
from execution_testing.test_types import Environment, Withdrawal


class HashMismatchExceptionError(Exception):
    """Exception raised when the expected and actual hashes don't match."""

    def __init__(
        self,
        expected_hash: str,
        actual_hash: str,
        message: str = "Hashes do not match",
    ) -> None:
        """Initialize the exception with the expected and actual hashes."""
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return the error message."""
        return f"{self.message}: Expected {self.expected_hash}, got {self.actual_hash}"


def verify_result(result: Result, env: Environment) -> None:
    """
    Verify that values in the t8n result match the expected values. Raises
    exception on unexpected values.
    """
    if env.withdrawals is not None:
        assert result.withdrawals_root == to_hex(
            Withdrawal.list_root(env.withdrawals)
        )


@unique
class OpMode(StrEnum):
    """Operation mode for the fill and execute."""

    CONSENSUS = "consensus"
    BENCHMARKING = "benchmarking"
    OPTIMIZE_GAS = "optimize-gas"
    OPTIMIZE_GAS_POST_PROCESSING = "optimize-gas-post-processing"


class BaseTest(BaseModel):
    """
    Represents a base Ethereum test which must return a single test fixture.
    """

    model_config = ConfigDict(extra="forbid")

    tag: str = ""
    fork: Fork = (
        BaseFork  # type: ignore[type-abstract]
        # default to BaseFork to allow the filler to set it,
        # instead of each test having to set it
    )

    _request: pytest.FixtureRequest | None = PrivateAttr(None)
    _operation_mode: OpMode | None = PrivateAttr(None)
    _gas_optimization: int | None = PrivateAttr(None)
    _gas_optimization_max_gas_limit: int | None = PrivateAttr(None)
    _opcode_count: OpcodeCount | None = PrivateAttr(None)

    expected_benchmark_gas_used: int | None = None
    skip_gas_used_validation: bool = False

    spec_types: ClassVar[Dict[str, Type["BaseTest"]]] = {}

    # Transition tool specific fields
    t8n_dump_dir: Path | None = Field(None, exclude=True)
    t8n_call_counter: int = Field(0, exclude=True)

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = []
    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = []

    supported_markers: ClassVar[Dict[str, str]] = {}

    def model_post_init(self, __context: Any, /) -> None:
        """
        Model post-init to assert that the custom pre-allocation was
        provided and the default was not used.
        """
        super().model_post_init(__context)
        assert self.fork != BaseFork, (
            "Fork was not provided by the filler/executor."
        )

    @classmethod
    def discard_fixture_format_by_marks(
        cls,
        fixture_format: FixtureFormat,
        fork: Fork,
        markers: List[pytest.Mark],
    ) -> bool:
        """
        Discard a fixture format from filling if the appropriate marker is
        used.
        """
        del fork, fixture_format, markers
        return False

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        Register all subclasses of BaseFixture with a fixture format name set
        as possible fixture formats.
        """
        if cls.pytest_parameter_name():
            # Register the new fixture format
            BaseTest.spec_types[cls.pytest_parameter_name()] = cls

    @classmethod
    def from_test(
        cls: Type[Self],
        *,
        base_test: "BaseTest",
        **kwargs: Any,
    ) -> Self:
        """Create a test in a different format from a base test."""
        new_instance = cls(
            tag=base_test.tag,
            fork=base_test.fork,
            t8n_dump_dir=base_test.t8n_dump_dir,
            expected_benchmark_gas_used=base_test.expected_benchmark_gas_used,
            skip_gas_used_validation=base_test.skip_gas_used_validation,
            **kwargs,
        )
        new_instance._request = base_test._request
        new_instance._operation_mode = base_test._operation_mode
        new_instance._opcode_count = base_test._opcode_count
        return new_instance

    @classmethod
    def discard_execute_format_by_marks(
        cls,
        execute_format: ExecuteFormat,
        fork: Fork,
        markers: List[pytest.Mark],
    ) -> bool:
        """
        Discard an execute format from executing if the appropriate marker is
        used.
        """
        del execute_format, fork, markers
        return False

    @abstractmethod
    def generate(
        self,
        *,
        t8n: TransitionTool,
        fixture_format: FixtureFormat,
    ) -> BaseFixture:
        """Generate the list of test fixtures."""
        pass

    def execute(
        self,
        *,
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
        return reduce(
            lambda x, y: x + ("_" if y.isupper() else "") + y, cls.__name__
        ).lower()

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
            has_benchmark_marker = (
                node.get_closest_marker("benchmark") is not None
            )
            return has_slow_marker or has_benchmark_marker
        return False

    def is_exception_test(self) -> bool | None:
        """
        Check if the test is an exception test (invalid block, invalid
        transaction).

        `None` is returned if it's not possible to determine if the test is
        negative or not. This is the case when the test is not run in pytest.
        """
        if self._request is not None and hasattr(self._request, "node"):
            return (
                self._request.node.get_closest_marker("exception_test")
                is not None
            )
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
    ) -> None:
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

    def get_genesis_environment(self) -> Environment:
        """
        Get the genesis environment for pre-allocation groups.

        Must be implemented by subclasses to provide the appropriate
        environment.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement genesis environment access for use with "
            "pre-allocation groups."
        )

    def update_pre_alloc_groups(
        self, pre_alloc_group_builders: PreAllocGroupBuilders, test_id: str
    ) -> None:
        """
        Create or update the pre-allocation group with the pre from the current
        spec.
        """
        if not hasattr(self, "pre"):
            raise AttributeError(
                f"{self.__class__.__name__} does not have a 'pre' field. Pre-allocation groups "
                "are only supported for test types that define pre-allocation."
            )
        pre_alloc_hash = self.compute_pre_alloc_group_hash()
        pre_alloc_group_builders.add_test_pre(
            pre_alloc_hash=pre_alloc_hash,
            test_id=str(test_id),
            fork=self.fork,
            environment=self.get_genesis_environment(),
            pre=self.pre,
        )

    def compute_pre_alloc_group_hash(self) -> str:
        """Hash (fork, env) in order to group tests by genesis config."""
        if not hasattr(self, "pre"):
            raise AttributeError(
                f"{self.__class__.__name__} does not have a 'pre' field. Pre-allocation group "
                "usage is only supported for test types that define pre-allocs."
            )
        fork_digest = hashlib.sha256(self.fork.name().encode("utf-8")).digest()
        fork_hash = int.from_bytes(fork_digest[:8], byteorder="big")
        genesis_env = self.get_genesis_environment()
        combined_hash = fork_hash ^ hash(genesis_env)

        # Check if test has pre_alloc_group marker
        if self._request is not None and hasattr(self._request, "node"):
            pre_alloc_group_marker = self._request.node.get_closest_marker(
                "pre_alloc_group"
            )
            if pre_alloc_group_marker:
                # Get the group name/salt from marker args
                if pre_alloc_group_marker.args:
                    group_salt = str(pre_alloc_group_marker.args[0])
                    if group_salt == "separate":
                        # Use nodeid for unique group per test
                        group_salt = self._request.node.nodeid
                    # Add custom salt to hash
                    salt_hash = hashlib.sha256(
                        group_salt.encode("utf-8")
                    ).digest()
                    salt_int = int.from_bytes(salt_hash[:8], byteorder="big")
                    combined_hash = combined_hash ^ salt_int

        return f"0x{combined_hash:016x}"


TestSpec = Callable[[Fork], Generator[BaseTest, None, None]]
