"""Tests for trace comparator types and ABC."""

import pytest

from execution_testing.base_types import HexNumber
from execution_testing.client_clis.cli_types import (
    TraceLine,
    Traces,
    TransactionTraces,
)
from execution_testing.client_clis.trace_comparators import (
    ExactNoGasTraceComparator,
    ExactTraceComparator,
    TraceComparator,
    TraceComparatorType,
    TraceComparisonResult,
    TraceDifference,
    TransactionCountMismatch,
    create_comparator,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def trace_line() -> TraceLine:
    """Return a default TraceLine."""
    return _make_trace_line()


@pytest.fixture()
def transaction_traces(trace_line: TraceLine) -> TransactionTraces:
    """Return a default TransactionTraces with one trace line."""
    return _make_transaction_traces([trace_line])


@pytest.fixture()
def traces(transaction_traces: TransactionTraces) -> Traces:
    """Return a default Traces with one transaction."""
    return _make_traces([transaction_traces])


@pytest.fixture()
def spy_comparator() -> "_SpyComparator":
    """Return a spy comparator that records calls."""
    return _SpyComparator()


@pytest.fixture()
def failing_comparator() -> "_FailingComparator":
    """Return a comparator that always reports a difference."""
    return _FailingComparator()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_trace_line(**overrides: object) -> TraceLine:
    """Create a TraceLine with sensible defaults."""
    defaults = {
        "pc": 0,
        "op": 0x60,
        "gas": 0x5F5E100,
        "gas_cost": 0x3,
        "mem_size": 0,
        "stack": [],
        "depth": 1,
        "refund": 0,
        "op_name": "PUSH1",
    }
    defaults.update(overrides)
    return TraceLine.model_validate(defaults)


def _make_transaction_traces(
    trace_lines: list[TraceLine] | None = None,
    output: str | None = "0x",
) -> TransactionTraces:
    """Create a TransactionTraces with default trace lines."""
    if trace_lines is None:
        trace_lines = [_make_trace_line()]
    return TransactionTraces.model_validate(
        {"traces": trace_lines, "output": output}
    )


def _make_traces(
    transactions: list[TransactionTraces] | None = None,
) -> Traces:
    """Create a Traces object."""
    if transactions is None:
        transactions = [_make_transaction_traces()]
    return Traces(root=transactions)


class _SpyComparator(TraceComparator):
    """Concrete subclass that records calls for testing the ABC."""

    @property
    def name(self) -> str:
        """Return the comparator's name."""
        return "spy"

    def __init__(self) -> None:
        self.calls: list[tuple[int]] = []

    def compare_transaction_traces(
        self,
        baseline: TransactionTraces,  # noqa: ARG002
        current: TransactionTraces,  # noqa: ARG002
        transaction_index: int,
    ) -> TraceComparisonResult:
        self.calls.append((transaction_index,))
        return TraceComparisonResult(equivalent=True, differences=[])


class _FailingComparator(TraceComparator):
    """Concrete subclass that always reports a difference."""

    @property
    def name(self) -> str:
        """Return the comparator's name."""
        return "failing"

    def compare_transaction_traces(
        self,
        baseline: TransactionTraces,  # noqa: ARG002
        current: TransactionTraces,  # noqa: ARG002
        transaction_index: int,
    ) -> TraceComparisonResult:
        return TraceComparisonResult(
            equivalent=False,
            differences=[
                TraceDifference(
                    transaction_index=transaction_index,
                    trace_line_index=0,
                    baseline="PUSH1 (pc=0)",
                    current="PUSH1 (pc=1)",
                )
            ],
        )


# ---------------------------------------------------------------------------
# Phase 1: Types and ABC
# ---------------------------------------------------------------------------


class TestTraceDifference:
    """Test TraceDifference dataclass."""

    def test_construction_and_field_access(self) -> None:
        """Verify all fields are accessible after construction."""
        diff = TraceDifference(
            transaction_index=2,
            trace_line_index=5,
            baseline="PUSH1 (pc=0xa)",
            current="PUSH1 (pc=0x14)",
        )
        assert diff.transaction_index == 2
        assert diff.trace_line_index == 5
        assert "PUSH1" in diff.baseline
        assert "PUSH1" in diff.current


class TestTransactionCountMismatch:
    """Test TransactionCountMismatch subclass."""

    def test_is_trace_difference_subclass(self) -> None:
        """Verify it is a TraceDifference subclass."""
        mismatch = TransactionCountMismatch(baseline_count=3, current_count=2)
        assert isinstance(mismatch, TraceDifference)

    def test_stores_counts(self) -> None:
        """Verify baseline and current counts are stored."""
        mismatch = TransactionCountMismatch(baseline_count=3, current_count=2)
        assert mismatch.baseline_count == 3
        assert mismatch.current_count == 2


class TestTraceComparisonResult:
    """Test TraceComparisonResult dataclass."""

    def test_equivalent_when_no_differences(self) -> None:
        """Result is equivalent when differences list is empty."""
        result = TraceComparisonResult(equivalent=True, differences=[])
        assert result.equivalent is True
        assert result.differences == []

    def test_not_equivalent_when_differences_exist(self) -> None:
        """Result is not equivalent when differences list is non-empty."""
        diff = TraceDifference(
            transaction_index=0,
            trace_line_index=0,
            baseline="PUSH1",
            current="PUSH2",
        )
        result = TraceComparisonResult(equivalent=False, differences=[diff])
        assert result.equivalent is False
        assert len(result.differences) == 1


class TestTraceComparatorType:
    """Test TraceComparatorType enum."""

    @pytest.mark.parametrize(
        "member,value",
        [
            (TraceComparatorType.EXACT, "exact"),
            (TraceComparatorType.EXACT_NO_GAS, "exact-no-gas"),
        ],
    )
    def test_enum_values(
        self, member: TraceComparatorType, value: str
    ) -> None:
        """Verify enum member values."""
        assert member == value


class TestTraceComparatorABC:
    """Test TraceComparator base class compare_traces logic."""

    def test_identical_traces_are_equivalent(
        self, traces: Traces, spy_comparator: _SpyComparator
    ) -> None:
        """Two identical Traces objects produce an equivalent result."""
        result = spy_comparator.compare_traces(traces, traces)
        assert result.equivalent is True
        assert result.differences == []

    def test_mismatched_transaction_count(
        self, spy_comparator: _SpyComparator
    ) -> None:
        """Different transaction counts produce a TransactionCountMismatch."""
        baseline = _make_traces(
            [
                _make_transaction_traces(),
                _make_transaction_traces(),
            ]
        )
        current = _make_traces([_make_transaction_traces()])
        result = spy_comparator.compare_traces(baseline, current)
        assert result.equivalent is False
        assert len(result.differences) == 1
        diff = result.differences[0]
        assert isinstance(diff, TransactionCountMismatch)
        assert diff.baseline_count == 2
        assert diff.current_count == 1

    def test_delegates_to_compare_transaction_traces(
        self, spy_comparator: _SpyComparator
    ) -> None:
        """Base class calls compare_transaction_traces for each pair."""
        tx1 = _make_transaction_traces()
        tx2 = _make_transaction_traces()
        baseline = _make_traces([tx1, tx2])
        current = _make_traces([tx1, tx2])
        spy_comparator.compare_traces(baseline, current)
        assert len(spy_comparator.calls) == 2
        assert spy_comparator.calls[0] == (0,)
        assert spy_comparator.calls[1] == (1,)

    def test_aggregates_differences_from_subclass(
        self, failing_comparator: _FailingComparator
    ) -> None:
        """Base class aggregates differences returned by the subclass."""
        baseline = _make_traces([_make_transaction_traces()])
        current = _make_traces([_make_transaction_traces()])
        result = failing_comparator.compare_traces(baseline, current)
        assert result.equivalent is False
        assert len(result.differences) == 1

    def test_empty_traces_are_equivalent(
        self, spy_comparator: _SpyComparator
    ) -> None:
        """Two empty Traces objects are equivalent."""
        baseline = _make_traces([])
        current = _make_traces([])
        result = spy_comparator.compare_traces(baseline, current)
        assert result.equivalent is True
        assert spy_comparator.calls == []

    def test_single_transaction_delegates_once(
        self, spy_comparator: _SpyComparator
    ) -> None:
        """Single transaction pair calls compare_transaction_traces once."""
        baseline = _make_traces([_make_transaction_traces()])
        current = _make_traces([_make_transaction_traces()])
        spy_comparator.compare_traces(baseline, current)
        assert len(spy_comparator.calls) == 1
        assert spy_comparator.calls[0] == (0,)


class TestCreateComparator:
    """Test the create_comparator factory function."""

    @pytest.mark.parametrize(
        "comparator_type,expected_name",
        [
            (TraceComparatorType.EXACT, "exact"),
            (TraceComparatorType.EXACT_NO_GAS, "exact-no-gas"),
        ],
    )
    def test_create_supported_comparators(
        self, comparator_type: TraceComparatorType, expected_name: str
    ) -> None:
        """Factory creates the right comparator for supported types."""
        comparator = create_comparator(comparator_type)
        assert comparator.name == expected_name


# ---------------------------------------------------------------------------
# Phase 2: TraceLine.compare(), TransactionTraces.compare(),
#           ExactTraceComparator
# ---------------------------------------------------------------------------


class TestTraceLineCompare:
    """Test TraceLine.compare() and are_equivalent()."""

    def test_gas_excluded_by_default(self) -> None:
        """Gas-only difference produces empty diffs with defaults."""
        baseline = _make_trace_line(gas=0x100)
        current = _make_trace_line(gas=0x200)
        b_diff, c_diff = baseline.compare(current)
        assert b_diff == {}
        assert c_diff == {}

    def test_custom_exclude_fields(self) -> None:
        """Custom exclude_fields skips specified fields only."""
        baseline = _make_trace_line(pc=0, gas=0x100)
        current = _make_trace_line(pc=5, gas=0x200)
        b_diff, c_diff = baseline.compare(current, exclude_fields={"pc"})
        assert "pc" not in b_diff
        assert "gas" in b_diff

    def test_are_equivalent_with_custom_exclude(self) -> None:
        """are_equivalent respects custom exclude_fields."""
        baseline = _make_trace_line(pc=0, gas=0x100)
        current = _make_trace_line(pc=0, gas=0x200)
        # Default excludes gas → equivalent
        assert baseline.are_equivalent(current)
        # Exclude nothing → not equivalent
        assert not baseline.are_equivalent(current, exclude_fields=set())


class TestTransactionTracesCompare:
    """Test TransactionTraces.compare() shared method."""

    def test_identical_traces_empty_diffs(self) -> None:
        """Two identical TransactionTraces produce no diffs."""
        tx = _make_transaction_traces()
        assert tx.compare(tx) == []

    def test_different_trace_lengths(self) -> None:
        """Different trace lengths return a structural diff."""
        baseline = _make_transaction_traces(
            [_make_trace_line(), _make_trace_line()]
        )
        current = _make_transaction_traces([_make_trace_line()])
        diffs = baseline.compare(current)
        assert len(diffs) == 1
        assert diffs[0].line_index is None
        assert "trace_length" in diffs[0].baseline_fields

    def test_different_output(self) -> None:
        """Different output returns a structural diff."""
        baseline = _make_transaction_traces(output="0xaa")
        current = _make_transaction_traces(output="0xbb")
        diffs = baseline.compare(current)
        assert any(
            d.line_index is None and "output" in d.baseline_fields
            for d in diffs
        )

    def test_different_gas_used_without_post_processing(self) -> None:
        """Different gas_used is reported when not post-processing."""
        baseline = _make_transaction_traces()
        current = _make_transaction_traces()
        baseline.gas_used = HexNumber(0x5208)
        current.gas_used = HexNumber(0x6000)
        diffs = baseline.compare(current, enable_post_processing=False)
        assert any(
            d.line_index is None and "gas_used" in d.baseline_fields
            for d in diffs
        )

    def test_different_gas_used_with_post_processing(self) -> None:
        """Different gas_used is ignored when post-processing."""
        baseline = _make_transaction_traces()
        current = _make_transaction_traces()
        baseline.gas_used = HexNumber(0x5208)
        current.gas_used = HexNumber(0x6000)
        diffs = baseline.compare(current, enable_post_processing=True)
        assert not any(
            d.line_index is None and "gas_used" in d.baseline_fields
            for d in diffs
        )

    def test_single_field_diff_on_line(self) -> None:
        """Single-field difference on a line returns line index and fields."""
        baseline = _make_transaction_traces([_make_trace_line(pc=0)])
        current = _make_transaction_traces([_make_trace_line(pc=5)])
        diffs = baseline.compare(current)
        assert len(diffs) == 1
        assert diffs[0].line_index == 0
        assert "pc" in diffs[0].baseline_fields
        assert "pc" in diffs[0].current_fields

    def test_multiple_fields_diff_on_one_line(self) -> None:
        """Multiple field diffs on one line are grouped together."""
        baseline = _make_transaction_traces([_make_trace_line(pc=0, op=0x60)])
        current = _make_transaction_traces([_make_trace_line(pc=5, op=0x61)])
        diffs = baseline.compare(current)
        assert len(diffs) == 1
        assert "pc" in diffs[0].baseline_fields
        assert "op" in diffs[0].baseline_fields

    def test_exclude_fields(self) -> None:
        """Excluded fields are not reported."""
        baseline = _make_transaction_traces(
            [_make_trace_line(gas=0x100, pc=0)]
        )
        current = _make_transaction_traces([_make_trace_line(gas=0x200, pc=5)])
        diffs = baseline.compare(current, exclude_fields={"gas", "gas_cost"})
        assert len(diffs) == 1
        assert "pc" in diffs[0].baseline_fields
        assert "gas" not in diffs[0].baseline_fields

    def test_exclude_fields_all_diffs_excluded(self) -> None:
        """When all differing fields are excluded, no diffs reported."""
        baseline = _make_transaction_traces([_make_trace_line(gas=0x100)])
        current = _make_transaction_traces([_make_trace_line(gas=0x200)])
        diffs = baseline.compare(current, exclude_fields={"gas", "gas_cost"})
        assert diffs == []

    def test_post_processing_removes_gas_stack_pollution(self) -> None:
        """GAS opcode stack pollution is cleaned with post-processing."""
        # GAS opcode pushes remaining gas onto stack; next line has it
        gas_line = _make_trace_line(
            pc=0, op=0x5A, op_name="GAS", depth=1, stack=[]
        )
        # Next line: stack has gas value (differs between runs)
        next_line_baseline = _make_trace_line(
            pc=1,
            op=0x60,
            op_name="PUSH1",
            depth=1,
            stack=[0xAAAA],
        )
        next_line_current = _make_trace_line(
            pc=1,
            op=0x60,
            op_name="PUSH1",
            depth=1,
            stack=[0xBBBB],
        )
        baseline = _make_transaction_traces([gas_line, next_line_baseline])
        current = _make_transaction_traces([gas_line, next_line_current])
        # Without post-processing: stack differs
        diffs_no_pp = baseline.compare(
            current,
            exclude_fields={"gas", "gas_cost"},
            enable_post_processing=False,
        )
        assert len(diffs_no_pp) == 1
        assert "stack" in diffs_no_pp[0].baseline_fields

        # With post-processing: GAS result nullified, equivalent
        diffs_pp = baseline.compare(
            current,
            exclude_fields={"gas", "gas_cost"},
            enable_post_processing=True,
        )
        assert diffs_pp == []


class TestTransactionTracesAreEquivalentRegression:
    """Regression tests for are_equivalent() after refactoring."""

    def test_identical_traces_equivalent(self) -> None:
        """Identical traces are equivalent."""
        tx = _make_transaction_traces()
        assert tx.are_equivalent(tx, enable_post_processing=False)

    def test_different_length_not_equivalent(self) -> None:
        """Different lengths are not equivalent."""
        baseline = _make_transaction_traces(
            [_make_trace_line(), _make_trace_line()]
        )
        current = _make_transaction_traces([_make_trace_line()])
        assert not baseline.are_equivalent(
            current, enable_post_processing=False
        )

    def test_different_output_not_equivalent(self) -> None:
        """Different output is not equivalent."""
        baseline = _make_transaction_traces(output="0xaa")
        current = _make_transaction_traces(output="0xbb")
        assert not baseline.are_equivalent(
            current, enable_post_processing=False
        )

    def test_gas_only_difference_is_equivalent(self) -> None:
        """Gas-only difference is equivalent (gas excluded by default)."""
        baseline = _make_transaction_traces([_make_trace_line(gas=0x100)])
        current = _make_transaction_traces([_make_trace_line(gas=0x200)])
        assert baseline.are_equivalent(current, enable_post_processing=False)

    def test_pc_difference_not_equivalent(self) -> None:
        """Non-gas field difference is not equivalent."""
        baseline = _make_transaction_traces([_make_trace_line(pc=0)])
        current = _make_transaction_traces([_make_trace_line(pc=5)])
        assert not baseline.are_equivalent(
            current, enable_post_processing=False
        )

    def test_gas_used_checked_without_post_processing(self) -> None:
        """gas_used difference is caught without post-processing."""
        baseline = _make_transaction_traces()
        current = _make_transaction_traces()
        baseline.gas_used = HexNumber(0x5208)
        current.gas_used = HexNumber(0x6000)
        assert not baseline.are_equivalent(
            current, enable_post_processing=False
        )

    def test_gas_used_ignored_with_post_processing(self) -> None:
        """gas_used difference is ignored with post-processing."""
        baseline = _make_transaction_traces()
        current = _make_transaction_traces()
        baseline.gas_used = HexNumber(0x5208)
        current.gas_used = HexNumber(0x6000)
        assert baseline.are_equivalent(current, enable_post_processing=True)


class TestExactTraceComparator:
    """Test ExactTraceComparator.compare_transaction_traces."""

    @pytest.fixture()
    def comparator(self) -> ExactTraceComparator:
        """Return an ExactTraceComparator."""
        return ExactTraceComparator()

    def test_identical_traces_are_equivalent(
        self, comparator: ExactTraceComparator
    ) -> None:
        """Two identical TransactionTraces produce an equivalent result."""
        tx = _make_transaction_traces()
        result = comparator.compare_transaction_traces(tx, tx, 0)
        assert result.equivalent is True
        assert result.differences == []

    @pytest.mark.parametrize(
        "field,baseline_val,current_val",
        [
            ("pc", 0, 5),
            ("op", 0x60, 0x61),
            ("gas", 0x100, 0x200),
            ("gas_cost", 0x3, 0x5),
        ],
        ids=["pc", "op", "gas", "gas_cost"],
    )
    def test_single_field_difference(
        self,
        comparator: ExactTraceComparator,
        field: str,
        baseline_val: int,
        current_val: int,
    ) -> None:
        """Single-field differences are detected."""
        baseline = _make_transaction_traces(
            [_make_trace_line(**{field: baseline_val})]
        )
        current = _make_transaction_traces(
            [_make_trace_line(**{field: current_val})]
        )
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is False
        assert len(result.differences) == 1
        assert result.differences[0].transaction_index == 0
        assert result.differences[0].trace_line_index == 0

    def test_differing_stack(self, comparator: ExactTraceComparator) -> None:
        """Different stack values are detected."""
        baseline = _make_transaction_traces(
            [_make_trace_line(stack=[0x1, 0x2])]
        )
        current = _make_transaction_traces(
            [_make_trace_line(stack=[0x1, 0x3])]
        )
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is False
        assert "stack" in result.differences[0].baseline

    def test_different_trace_lengths(
        self, comparator: ExactTraceComparator
    ) -> None:
        """Different trace lengths produce a trace_length diff."""
        baseline = _make_transaction_traces(
            [_make_trace_line(), _make_trace_line()]
        )
        current = _make_transaction_traces([_make_trace_line()])
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is False
        diff = result.differences[0]
        assert "trace_length" in diff.baseline
        assert "trace_length" in diff.current

    def test_different_output(self, comparator: ExactTraceComparator) -> None:
        """Different output field is detected."""
        baseline = _make_transaction_traces(output="0xaa")
        current = _make_transaction_traces(output="0xbb")
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is False
        diff = result.differences[0]
        assert "0xaa" in diff.baseline
        assert "0xbb" in diff.current

    def test_multiple_differences_in_one_transaction(
        self, comparator: ExactTraceComparator
    ) -> None:
        """Multiple field diffs on one line produce one TraceDifference."""
        baseline = _make_transaction_traces([_make_trace_line(pc=0, op=0x60)])
        current = _make_transaction_traces([_make_trace_line(pc=5, op=0x61)])
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is False
        # One TraceDifference per line, with all differing fields
        assert len(result.differences) == 1
        assert "pc" in result.differences[0].baseline
        assert "op" in result.differences[0].baseline

    def test_assembly_format_baseline_and_current(
        self, comparator: ExactTraceComparator
    ) -> None:
        """Diff strings contain opcode name and differing field values."""
        baseline = _make_transaction_traces([_make_trace_line(pc=0)])
        current = _make_transaction_traces([_make_trace_line(pc=5)])
        result = comparator.compare_transaction_traces(baseline, current, 0)
        diff = result.differences[0]
        assert diff.baseline.startswith("PUSH1")
        assert diff.current.startswith("PUSH1")
        assert "pc=" in diff.baseline
        assert "pc=" in diff.current

    def test_full_compare_traces_multi_transaction(
        self, comparator: ExactTraceComparator
    ) -> None:
        """Integration: multi-tx Traces with one differing tx."""
        identical_tx = _make_transaction_traces([_make_trace_line(pc=0)])
        baseline_diff_tx = _make_transaction_traces([_make_trace_line(pc=10)])
        current_diff_tx = _make_transaction_traces([_make_trace_line(pc=20)])
        baseline = _make_traces([identical_tx, baseline_diff_tx])
        current = _make_traces([identical_tx, current_diff_tx])
        result = comparator.compare_traces(baseline, current)
        assert result.equivalent is False
        assert all(d.transaction_index == 1 for d in result.differences)


# ---------------------------------------------------------------------------
# Phase 3: ExactNoGasTraceComparator
# ---------------------------------------------------------------------------


class TestExactNoGasTraceComparator:
    """Test ExactNoGasTraceComparator.compare_transaction_traces."""

    @pytest.fixture()
    def comparator(self) -> ExactNoGasTraceComparator:
        """Return an ExactNoGasTraceComparator."""
        return ExactNoGasTraceComparator()

    @pytest.mark.parametrize(
        "field",
        ["gas", "gas_cost"],
        ids=["gas_only", "gas_cost_only"],
    )
    def test_gas_field_difference_is_equivalent(
        self, comparator: ExactNoGasTraceComparator, field: str
    ) -> None:
        """Traces differing only in gas or gas_cost are equivalent."""
        baseline = _make_transaction_traces(
            [_make_trace_line(**{field: 0x100})]
        )
        current = _make_transaction_traces(
            [_make_trace_line(**{field: 0x200})]
        )
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is True

    def test_gas_and_non_gas_difference(
        self, comparator: ExactNoGasTraceComparator
    ) -> None:
        """Gas diff ignored but non-gas diff (op_name) reported."""
        baseline = _make_transaction_traces(
            [_make_trace_line(gas=0x100, op_name="PUSH1")]
        )
        current = _make_transaction_traces(
            [_make_trace_line(gas=0x200, op_name="PUSH2")]
        )
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is False
        diff = result.differences[0]
        assert "op_name" in diff.baseline
        assert "gas" not in diff.baseline

    def test_stack_difference_detected(
        self, comparator: ExactNoGasTraceComparator
    ) -> None:
        """Non-gas fields like stack are still checked."""
        baseline = _make_transaction_traces([_make_trace_line(stack=[0x1])])
        current = _make_transaction_traces([_make_trace_line(stack=[0x2])])
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is False
        assert "stack" in result.differences[0].baseline

    def test_length_mismatch(
        self, comparator: ExactNoGasTraceComparator
    ) -> None:
        """Different trace lengths are detected."""
        baseline = _make_transaction_traces(
            [_make_trace_line(), _make_trace_line()]
        )
        current = _make_transaction_traces([_make_trace_line()])
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is False
        assert "trace_length" in result.differences[0].baseline

    def test_output_mismatch(
        self, comparator: ExactNoGasTraceComparator
    ) -> None:
        """Different output field is detected."""
        baseline = _make_transaction_traces(output="0xaa")
        current = _make_transaction_traces(output="0xbb")
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is False
        assert "0xaa" in result.differences[0].baseline

    def test_gas_used_difference_is_equivalent(
        self, comparator: ExactNoGasTraceComparator
    ) -> None:
        """gas_used difference is ignored (post-processing enabled)."""
        baseline = _make_transaction_traces()
        current = _make_transaction_traces()
        baseline.gas_used = HexNumber(0x5208)
        current.gas_used = HexNumber(0x6000)
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is True
        assert result.differences == []

    def test_gas_stack_pollution_is_equivalent(
        self, comparator: ExactNoGasTraceComparator
    ) -> None:
        """GAS opcode stack pollution is cleaned by remove_gas()."""
        gas_line = _make_trace_line(
            pc=0, op=0x5A, op_name="GAS", depth=1, stack=[]
        )
        next_baseline = _make_trace_line(
            pc=1,
            op=0x60,
            op_name="PUSH1",
            depth=1,
            stack=[0xAAAA],
        )
        next_current = _make_trace_line(
            pc=1,
            op=0x60,
            op_name="PUSH1",
            depth=1,
            stack=[0xBBBB],
        )
        baseline = _make_transaction_traces([gas_line, next_baseline])
        current = _make_transaction_traces([gas_line, next_current])
        result = comparator.compare_transaction_traces(baseline, current, 0)
        assert result.equivalent is True
        assert result.differences == []
