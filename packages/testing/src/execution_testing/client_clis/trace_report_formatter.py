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
    ) -> str | None:
        """Format one test's comparison results.

        Return None if there is nothing to report (e.g. all equivalent).
        """
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
    ) -> str | None:
        """Format one test's comparison results.

        Return None if all comparators are equivalent.
        """
        diff_lines: list[str] = []
        for name, result in results.items():
            if result.equivalent:
                continue
            count = len(result.differences)
            diff_lines.append(f"  [{name}] DIFFERENT ({count} differences)")
            shown = result.differences[: self.max_differences]
            for diff in shown:
                loc = (
                    f"tx[{diff.transaction_index}] "
                    f"line[{diff.trace_line_index}]"
                )
                diff_lines.append(
                    f"    {loc} baseline: {diff.baseline}"
                )
                diff_lines.append(
                    f"    {loc} current:  {diff.current}"
                )
            remaining = count - len(shown)
            if remaining > 0:
                diff_lines.append(f"    ... ({remaining} more)")
        if not diff_lines:
            return None
        return "\n".join([f"{test_id}:"] + diff_lines)

    def format_summary(
        self,
        all_results: dict[str, dict[str, TraceComparisonResult]],
    ) -> str:
        """Format the aggregated report for all tests."""
        lines: list[str] = []
        with_diffs = 0
        for test_id, results in all_results.items():
            formatted = self.format_test_result(test_id, results)
            if formatted is not None:
                lines.append(formatted)
                lines.append("")
                with_diffs += 1

        total = len(all_results)
        lines.append(
            f"Summary: {total} tests verified, {with_diffs} with differences"
        )
        return "\n".join(lines)
