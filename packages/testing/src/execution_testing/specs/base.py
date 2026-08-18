"""
Base test class and helper functions for Ethereum state and blockchain tests.
"""

from abc import abstractmethod
from enum import StrEnum, unique
from functools import reduce
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Sequence,
    Tuple,
    Type,
)

import pytest
from _pytest.mark.structures import ParameterSet
from pydantic import BaseModel, ConfigDict, Field
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
)
from execution_testing.fixtures.post_verifications import PostVerifications
from execution_testing.forks import Fork, TransitionFork
from execution_testing.forks.base_fork import BaseFork
from execution_testing.test_types import Environment, Withdrawal
from execution_testing.test_types.receipt_types import (
    TransactionReceipt,
)


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
        return (
            f"{self.message}: Expected {self.expected_hash}, "
            f"got {self.actual_hash}"
        )


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


class FillResult(BaseModel):
    """
    Result of the filling operation, returned by the `generate` method.
    """

    fixture: BaseFixture
    gas_optimization: int | None
    benchmark_gas_used: int | None = None
    benchmark_block_gas_used: int | None = None
    benchmark_opcode_count: OpcodeCount | None = None
    post_verifications: PostVerifications | None = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def labeled_format_parameter_set(
    format_with_or_without_label: LabeledExecuteFormat
    | LabeledFixtureFormat
    | ExecuteFormat
    | FixtureFormat,
    primary_format: bool = False,
) -> ParameterSet:
    """
    Return a parameter set from a fixture/execute format and parse a label if
    there's any.

    The label will be used in the test id and also will be added as a marker to
    the generated test case when filling/executing the test.

    The format keeps its label, so a spec type that labels one format more
    than once can tell which of them it is filling. Call `format_class()` to
    strip the label.
    """
    return pytest.param(
        format_with_or_without_label,
        id=format_with_or_without_label.format_id(),
        marks=format_with_or_without_label.marks()
        + [
            pytest.mark.fixture_format_id(
                format_with_or_without_label.format_id()
            )
        ]
        + ([pytest.mark.primary_format] if primary_format else []),
    )


class BaseTest(BaseModel):
    """
    Represents a base Ethereum test which must return a single test fixture.
    """

    model_config = ConfigDict(extra="forbid")

    fork: Fork | TransitionFork = (
        BaseFork
        # default to BaseFork to allow the filler to set it,
        # instead of each test having to set it
    )
    operation_mode: OpMode | None = None
    sync_block: bool = False
    """
    Append framework-built empty blocks above a blockchain test's
    authored leaves, stored out-of-chain in the fixture's
    ``sync_payloads`` field, when filling a fixture format that carries
    them (currently ``blockchain_test_engine_x``).

    A sync-based consumer announces each appended block, which makes
    every representable payload the test author wrote an ancestor of at
    least one target the client must fetch and execute through its
    devp2p sync path. The test's own directives are filled exactly as
    written. Enabled unless ``--no-sync-block`` withholds them or the
    test itself opts out by passing ``sync_block=False``; see "Sync
    Payloads" in the filling-tests docs.
    """
    sync_block_salt: str = ""
    """
    Per-test value digested into each appended block's ``extra_data``.

    Two tests of one pre-allocation group may declare byte-identical
    payload graphs, and a client reused across the group only starts a
    sync for a head it has never seen; the salt keeps every appended
    block's hash unique to its test. Different leaves already have
    different parent hashes. The filler salts with the test's node id.
    """
    gas_optimization_max_gas_limit: int | None = None
    expected_benchmark_gas_used: int | None = None
    skip_gas_used_validation: bool = False
    expected_receipt_status: int | None = None
    is_tx_gas_heavy_test: bool = False
    is_exception_test: bool = False
    is_inclusion_test: bool = False

    # Class variables, to be set by subclasses
    spec_types: ClassVar[Dict[str, Type["BaseTest"]]] = {}
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
        fixture_format: FixtureFormat | LabeledFixtureFormat,
        markers: List[pytest.Mark],
    ) -> bool:
        """
        Discard a fixture format from filling if the appropriate marker is
        used.

        The format keeps its label: comparing it against a plain format
        matches every label of it, `format_id()` identifies a single one.
        """
        del fixture_format, markers
        return False

    @classmethod
    def fixture_format_parameters(
        cls,
        *,
        markers: List[pytest.Mark],
    ) -> List[Tuple[FixtureFormat | LabeledFixtureFormat, ParameterSet]]:
        """
        Return one pytest parameter per fixture format this spec type fills,
        paired with the format it fills, so the caller can narrow the formats
        down to the ones its session generates.

        The first format not vetoed by `discard_fixture_format_by_marks` is
        the primary and is marked `primary_format`, so `-m primary_format`
        fills each test once. Only sessions that generate a single format per
        test can filter that primary out, and there the marker is moot.

        An override that parametrizes further must leave exactly one parameter
        marked `primary_format`.
        """
        parameters: List[
            Tuple[FixtureFormat | LabeledFixtureFormat, ParameterSet]
        ] = []
        for format_with_or_without_label in cls.supported_fixture_formats:
            if cls.discard_fixture_format_by_marks(
                format_with_or_without_label,
                markers,
            ):
                continue
            parameter = labeled_format_parameter_set(
                format_with_or_without_label,
                primary_format=not parameters,
            )
            parameters.append((format_with_or_without_label, parameter))
        return parameters

    @classmethod
    def execute_format_parameters(
        cls,
    ) -> List[Tuple[LabeledExecuteFormat, ParameterSet]]:
        """
        Return one pytest parameter per execute format this spec type runs.

        Each element pairs the labeled format with the parameter that executes
        it, so the caller can inspect what the format requires of the session
        (e.g. an Engine RPC) and skip or select it accordingly.

        Formats are not vetoed here the way `fixture_format_parameters` vetoes
        them: `discard_execute_format_by_marks` needs the fork, which is only
        parametrized later, so the caller applies it during collection.

        Subclasses may override this to parametrize further, e.g. to execute a
        single execute format more than once.
        """
        return [
            (
                labeled_execute_format,
                labeled_format_parameter_set(labeled_execute_format),
            )
            for labeled_execute_format in cls.supported_execute_formats
        ]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        Register all subclasses of BaseFixture with a fixture format name set
        as possible fixture formats.
        """
        super().__pydantic_init_subclass__(**kwargs)

        # Don't register dynamically generated wrapper classes
        if getattr(cls, "__is_base_test_wrapper__", False):
            return

        if cls.pytest_parameter_name():
            # Register the new fixture format
            BaseTest.spec_types[cls.pytest_parameter_name()] = cls

    @classmethod
    def from_test(
        cls,
        *,
        base_test: "BaseTest",
        **kwargs: Any,
    ) -> Self:
        """Create a test in a different format from a base test."""
        for k in BaseTest.model_fields.keys():
            if k not in kwargs and k in base_test.model_fields_set:
                kwargs[k] = getattr(base_test, k)
        return cls(**kwargs)

    @classmethod
    def discard_execute_format_by_marks(
        cls,
        execute_format: ExecuteFormat | LabeledExecuteFormat,
        fork: Fork | TransitionFork,
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
        fixture_format: FixtureFormat | LabeledFixtureFormat,
    ) -> FillResult:
        """Generate the test fixture using the given fixture format."""
        pass

    def execute(
        self,
        *,
        execute_format: ExecuteFormat | LabeledExecuteFormat,
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

    def check_exception_test(
        self,
        *,
        exception: bool,
    ) -> None:
        """Compare the test marker against the outcome of the test."""
        if self.is_exception_test != exception:
            if exception:
                raise Exception(
                    "Test produced an invalid block or transaction but was "
                    "not marked with the `exception_test` marker. Add the "
                    "`@pytest.mark.exception_test` decorator to the test."
                )
            else:
                raise Exception(
                    "Test didn't produce an invalid block or transaction but "
                    "was marked with the `exception_test` marker. Remove the "
                    "`@pytest.mark.exception_test` decorator from the test."
                )

    def get_genesis_environment(self) -> Environment:
        """
        Get the genesis environment for pre-allocation groups.

        Must be implemented by subclasses to provide the appropriate
        environment.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement genesis environment "
            "access for use with pre-allocation groups."
        )

    def validate_benchmark_gas(
        self,
        *,
        benchmark_gas_used: int | None,
        gas_benchmark_value: int,
        benchmark_block_gas_used: int | None = None,
    ) -> None:
        """
        Validates the total consumed gas of the last block in the test matches
        the expectation of the benchmark test.

        ``benchmark_gas_used`` is the combined gas across all dimensions (the
        receipt ``cumulativeGasUsed``) and is checked against
        ``expected_benchmark_gas_used``. ``benchmark_block_gas_used`` is the
        block-header gas, i.e. the maximum across the independent gas
        dimensions (EIP-8037); it is what must stay within the block gas
        limit, because the combined value can legitimately exceed it. When it
        is not available (e.g. execute mode), the combined value is used for
        the ceiling check instead.

        Requires the following fields to be set:
        - expected_benchmark_gas_used
        - operation_mode
        """
        if self.operation_mode != OpMode.BENCHMARKING:
            return
        assert benchmark_gas_used is not None, "_benchmark_gas_used is not set"
        # Perform gas validation if required for benchmarking.
        # Ensures benchmark tests consume exactly the expected gas.
        if not self.skip_gas_used_validation:
            # Verify that the total gas consumed in the last block
            # matches expectations
            expected_benchmark_gas_used = self.expected_benchmark_gas_used
            if expected_benchmark_gas_used is None:
                expected_benchmark_gas_used = gas_benchmark_value
            diff = benchmark_gas_used - expected_benchmark_gas_used
            assert benchmark_gas_used == expected_benchmark_gas_used, (
                f"Total gas used ({benchmark_gas_used}) does not "
                "match expected benchmark gas "
                f"({expected_benchmark_gas_used}), "
                f"difference: {diff}"
            )
        # No single gas dimension may exceed the block gas limit. The
        # block-header gas is the max across dimensions; the combined
        # execution+state gas may exceed the target under EIP-8037, so the
        # ceiling is checked against the header value when available.
        block_gas_used = (
            benchmark_block_gas_used
            if benchmark_block_gas_used is not None
            else benchmark_gas_used
        )
        assert block_gas_used <= gas_benchmark_value, (
            f"benchmark block gas used ({block_gas_used}) exceeds maximum "
            "benchmark gas allowed for this configuration: "
            f"{gas_benchmark_value}"
        )

    def validate_receipt_status(
        self,
        *,
        receipts: List[TransactionReceipt],
        block_number: int,
    ) -> None:
        """
        Validate receipt status for every transaction in a block.

        When expected_receipt_status is set, verify that all
        receipts match. Catches silent OOG failures that roll
        back state and invalidate benchmarks.
        """
        if self.expected_receipt_status is None:
            return
        for i, receipt in enumerate(receipts):
            if receipt.status is not None and (
                int(receipt.status) != self.expected_receipt_status
            ):
                raise Exception(
                    f"Transaction {i} in block "
                    f"{block_number} has receipt "
                    f"status {int(receipt.status)}, "
                    f"expected "
                    f"{self.expected_receipt_status}."
                )


TestSpec = Callable[[Fork], Generator[BaseTest, None, None]]
