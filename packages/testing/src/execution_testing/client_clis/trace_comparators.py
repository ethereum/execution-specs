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
    differences: list[TraceDifference] = []
    for diff in raw_diffs:
        if diff.line_index is None:
            # Structural diff (trace_length, output, gas_used)
            b_str = ", ".join(
                f"{k}={v}" for k, v in diff.baseline_fields.items()
            )
            c_str = ", ".join(
                f"{k}={v}" for k, v in diff.current_fields.items()
            )
            differences.append(
                TraceDifference(
                    transaction_index=transaction_index,
                    trace_line_index=-1,
                    baseline=b_str,
                    current=c_str,
                )
            )
        else:
            b_line = baseline.traces[diff.line_index]
            c_line = current.traces[diff.line_index]
            differences.append(
                TraceDifference(
                    transaction_index=transaction_index,
                    trace_line_index=diff.line_index,
                    baseline=_format_trace_line_diff(
                        b_line, diff.baseline_fields
                    ),
                    current=_format_trace_line_diff(
                        c_line, diff.current_fields
                    ),
                )
            )
    return TraceComparisonResult(
        equivalent=len(differences) == 0,
        differences=differences,
    )


class ExactTraceComparator(TraceComparator):
    """Compare traces exactly, including gas fields."""

    @property
    def name(self) -> str:
        """Return the comparator's name."""
        return "exact"

    def compare_transaction_traces(
        self,
        baseline: TransactionTraces,
        current: TransactionTraces,
        transaction_index: int,
    ) -> TraceComparisonResult:
        """Compare all fields of each trace line pair."""
        return _build_result_from_compare(
            baseline,
            current,
            transaction_index,
        )


class ExactNoGasTraceComparator(TraceComparator):
    """Compare traces exactly, excluding gas and gas_cost fields."""

    @property
    def name(self) -> str:
        """Return the comparator's name."""
        return "exact-no-gas"

    def compare_transaction_traces(
        self,
        baseline: TransactionTraces,
        current: TransactionTraces,
        transaction_index: int,
    ) -> TraceComparisonResult:
        """Compare all fields except gas and gas_cost."""
        return _build_result_from_compare(
            baseline,
            current,
            transaction_index,
            exclude_fields={"gas", "gas_cost"},
            enable_post_processing=True,
        )


def create_comparator(
    comparator_type: TraceComparatorType,
) -> TraceComparator:
    """Create a comparator instance from the given type."""
    if comparator_type == TraceComparatorType.EXACT:
        return ExactTraceComparator()
    elif comparator_type == TraceComparatorType.EXACT_NO_GAS:
        return ExactNoGasTraceComparator()
    else:
        raise ValueError(f"Unknown comparator type: {comparator_type}")
