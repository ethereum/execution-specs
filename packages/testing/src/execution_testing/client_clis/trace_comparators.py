"""Trace comparators for verifying EVM execution traces against a baseline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum

from execution_testing.client_clis.cli_types import (
    TraceLine,
    Traces,
    TransactionTraces,
)


class TraceComparatorType(StrEnum):
    """Supported trace comparator strategies."""

    EXACT = "exact"
    EXACT_NO_GAS = "exact-no-gas"
    EXACT_NO_STACK = "exact-no-stack"
    EXACT_NO_STACK_NO_GAS = "exact-no-stack-no-gas"
    GAS_EXHAUSTION = "gas-exhaustion"


def _format_trace_line_diff(
    trace_line: TraceLine,
    differing_fields: dict[str, str],
) -> str:
    """
    Format a trace line as an assembly-like string with diffs.

    Return the opcode name, with differing field values in brackets
    if any non-opcode fields differ.
    Example: "PUSH1 (pc=0x3, stack=['0x4'])"
    """
    if not differing_fields:
        return trace_line.op_name
    fields_str = ", ".join(f"{k}={v}" for k, v in differing_fields.items())
    return f"{trace_line.op_name} ({fields_str})"


@dataclass
class TraceDifference:
    """A difference between baseline and current trace at a specific line."""

    transaction_index: int
    trace_line_index: int
    baseline: str
    current: str


@dataclass
class TransactionCountMismatch(TraceDifference):
    """Structural mismatch: different number of transactions."""

    transaction_index: int = 0
    trace_line_index: int = -1
    baseline: str = ""
    current: str = ""
    baseline_count: int = 0
    current_count: int = 0


@dataclass
class TraceComparisonResult:
    """Result of comparing two Traces objects."""

    equivalent: bool
    differences: list[TraceDifference] = field(default_factory=list)


class TraceComparator(ABC):
    """Abstract base class for trace comparison strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the comparator's name."""
        ...

    @abstractmethod
    def compare_transaction_traces(
        self,
        baseline: TransactionTraces,
        current: TransactionTraces,
        transaction_index: int,
    ) -> TraceComparisonResult:
        """Compare a single transaction's traces."""
        ...

    def compare_traces(
        self,
        baseline: Traces,
        current: Traces,
    ) -> TraceComparisonResult:
        """Compare two Traces objects by iterating transaction pairs."""
        if len(baseline.root) != len(current.root):
            return TraceComparisonResult(
                equivalent=False,
                differences=[
                    TransactionCountMismatch(
                        baseline_count=len(baseline.root),
                        current_count=len(current.root),
                    )
                ],
            )

        all_differences: list[TraceDifference] = []
        for i, (b_tx, c_tx) in enumerate(
            zip(baseline.root, current.root, strict=False)
        ):
            result = self.compare_transaction_traces(b_tx, c_tx, i)
            all_differences.extend(result.differences)

        return TraceComparisonResult(
            equivalent=len(all_differences) == 0,
            differences=all_differences,
        )


def _build_result_from_compare(
    baseline: TransactionTraces,
    current: TransactionTraces,
    transaction_index: int,
    exclude_fields: set[str] | None = None,
    enable_post_processing: bool = False,
) -> TraceComparisonResult:
    """
    Build a TraceComparisonResult from TransactionTraces.compare().

    Convert the raw diff tuples from compare() into TraceDifference
    objects with assembly-like strings.
    """
    raw_diffs = baseline.compare(
        current,
        exclude_fields=exclude_fields,
        enable_post_processing=enable_post_processing,
    )
    if not raw_diffs:
        return TraceComparisonResult(equivalent=True)

    # Only report the first difference: once traces diverge, subsequent
    # lines will mostly differ too.
    diff = raw_diffs[0]
    if diff.line_index is None:
        b_str = ", ".join(f"{k}={v}" for k, v in diff.baseline_fields.items())
        c_str = ", ".join(f"{k}={v}" for k, v in diff.current_fields.items())
        trace_diff = TraceDifference(
            transaction_index=transaction_index,
            trace_line_index=-1,
            baseline=b_str,
            current=c_str,
        )
    else:
        b_line = baseline.traces[diff.line_index]
        c_line = current.traces[diff.line_index]
        trace_diff = TraceDifference(
            transaction_index=transaction_index,
            trace_line_index=diff.line_index,
            baseline=_format_trace_line_diff(b_line, diff.baseline_fields),
            current=_format_trace_line_diff(c_line, diff.current_fields),
        )
    return TraceComparisonResult(
        equivalent=False,
        differences=[trace_diff],
    )


class FieldExclusionTraceComparator(TraceComparator):
    """Compare traces field-by-field, optionally excluding fields."""

    def __init__(
        self,
        comparator_name: str,
        exclude_fields: set[str] | None = None,
        enable_post_processing: bool = False,
    ) -> None:
        self._name = comparator_name
        self._exclude_fields = exclude_fields
        self._enable_post_processing = enable_post_processing

    @property
    def name(self) -> str:
        """Return the comparator's name."""
        return self._name

    def compare_transaction_traces(
        self,
        baseline: TransactionTraces,
        current: TransactionTraces,
        transaction_index: int,
    ) -> TraceComparisonResult:
        """Compare trace fields, excluding configured fields."""
        return _build_result_from_compare(
            baseline,
            current,
            transaction_index,
            exclude_fields=self._exclude_fields,
            enable_post_processing=self._enable_post_processing,
        )


def _is_out_of_gas_error(error: str | None) -> bool:
    """Return True if the error string indicates an out-of-gas condition."""
    if error is None:
        return False
    return "out of gas" in error.lower()


def _find_gas_exhaustion_points(
    tx: TransactionTraces,
) -> list[int]:
    """Return trace line indices where an out-of-gas error occurs."""
    return [
        i
        for i, line in enumerate(tx.traces)
        if _is_out_of_gas_error(line.error)
    ]


def _format_oog_trace_line(
    tx: TransactionTraces,
    line_index: int,
) -> str:
    """Format a trace line showing its error field for OOG reporting."""
    if line_index >= len(tx.traces):
        return "no trace line"
    line = tx.traces[line_index]
    return _format_trace_line_diff(line, {"error": str(line.error)})


class GasExhaustionTraceComparator(TraceComparator):
    """
    Detect differences in gas exhaustion between traces.

    Equivalent when both sides have no out-of-gas errors or when
    both run out of gas at the same trace line(s). Different when
    the out-of-gas points diverge.
    """

    @property
    def name(self) -> str:
        """Return the comparator's name."""
        return "gas-exhaustion"

    def compare_transaction_traces(
        self,
        baseline: TransactionTraces,
        current: TransactionTraces,
        transaction_index: int,
    ) -> TraceComparisonResult:
        """Compare gas exhaustion points between two transaction traces."""
        b_set = set(_find_gas_exhaustion_points(baseline))
        c_set = set(_find_gas_exhaustion_points(current))

        if b_set == c_set:
            return TraceComparisonResult(equivalent=True)

        differences: list[TraceDifference] = []
        for line_index in sorted(b_set - c_set):
            differences.append(
                TraceDifference(
                    transaction_index=transaction_index,
                    trace_line_index=line_index,
                    baseline=_format_oog_trace_line(baseline, line_index),
                    current="no out-of-gas",
                )
            )
        for line_index in sorted(c_set - b_set):
            differences.append(
                TraceDifference(
                    transaction_index=transaction_index,
                    trace_line_index=line_index,
                    baseline="no out-of-gas",
                    current=_format_oog_trace_line(current, line_index),
                )
            )

        return TraceComparisonResult(
            equivalent=False,
            differences=differences,
        )


_FIELD_EXCLUSION_CONFIGS: dict[
    TraceComparatorType,
    tuple[set[str] | None, bool],
] = {
    TraceComparatorType.EXACT: (None, False),
    TraceComparatorType.EXACT_NO_GAS: ({"gas"}, True),
    TraceComparatorType.EXACT_NO_STACK: ({"stack"}, False),
    TraceComparatorType.EXACT_NO_STACK_NO_GAS: ({"gas", "stack"}, False),
}


def create_comparator(
    comparator_type: TraceComparatorType,
) -> TraceComparator:
    """Create a comparator instance from the given type."""
    if comparator_type == TraceComparatorType.GAS_EXHAUSTION:
        return GasExhaustionTraceComparator()
    if comparator_type in _FIELD_EXCLUSION_CONFIGS:
        exclude_fields, post_processing = _FIELD_EXCLUSION_CONFIGS[
            comparator_type
        ]
        return FieldExclusionTraceComparator(
            comparator_type.value,
            exclude_fields=exclude_fields,
            enable_post_processing=post_processing,
        )
    raise ValueError(f"Unknown comparator type: {comparator_type}")
