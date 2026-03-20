"""Report formatters for trace comparison results."""

from abc import ABC, abstractmethod

from execution_testing.client_clis.trace_comparators import (
    TraceComparisonResult,
)


class TracesDiffReportFormatter(ABC):
    """Abstract base class for formatting trace comparison reports."""

    @abstractmethod
    def format_test_result(
        self,
        test_id: str,
        results: dict[str, TraceComparisonResult],
    ) -> str:
        """Format one test's comparison results across all comparators."""
        ...

    @abstractmethod
    def format_summary(
        self,
        all_results: dict[str, dict[str, TraceComparisonResult]],
    ) -> str:
        """Format the aggregated report for all tests."""
        ...


class TextTracesDiffReportFormatter(TracesDiffReportFormatter):
    """Human-readable plain text formatter."""

    def __init__(self, max_differences: int = 10) -> None:
        """Initialize with a cap on displayed differences per comparator."""
        self.max_differences = max_differences

    def format_test_result(
        self,
        test_id: str,
        results: dict[str, TraceComparisonResult],
    ) -> str:
        """Format one test's comparison results across all comparators."""
        lines = [f"{test_id}:"]
        for name, result in results.items():
            if result.equivalent:
                lines.append(f"  [{name}] EQUIVALENT")
            else:
                count = len(result.differences)
                lines.append(f"  [{name}] DIFFERENT ({count} differences)")
                shown = result.differences[: self.max_differences]
                for diff in shown:
                    loc = (
                        f"tx[{diff.transaction_index}] "
                        f"line[{diff.trace_line_index}]"
                    )
                    lines.append(f"    {loc} baseline: {diff.baseline}")
                    lines.append(f"    {loc} current:  {diff.current}")
                remaining = count - len(shown)
                if remaining > 0:
                    lines.append(f"    ... ({remaining} more)")
        return "\n".join(lines)

    def format_summary(
        self,
        all_results: dict[str, dict[str, TraceComparisonResult]],
    ) -> str:
        """Format the aggregated report for all tests."""
        lines = []
        for test_id, results in all_results.items():
            lines.append(self.format_test_result(test_id, results))
            lines.append("")

        total = len(all_results)
        with_diffs = sum(
            1
            for results in all_results.values()
            if any(not r.equivalent for r in results.values())
        )
        lines.append(
            f"Summary: {total} tests verified, {with_diffs} with differences"
        )
        return "\n".join(lines)
