"""Tests for trace report formatters."""

import json

import pytest

from execution_testing.client_clis.trace_comparators import (
    TraceComparisonResult,
    TraceDifference,
)
from execution_testing.client_clis.trace_report_formatter import (
    JsonTracesDiffReportFormatter,
    TextTracesDiffReportFormatter,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def formatter() -> TextTracesDiffReportFormatter:
    """Return a default formatter."""
    return TextTracesDiffReportFormatter()


def _make_result(
    equivalent: bool = True,
    differences: list[TraceDifference] | None = None,
) -> TraceComparisonResult:
    """Create a TraceComparisonResult."""
    return TraceComparisonResult(
        equivalent=equivalent,
        differences=differences or [],
    )


def _make_diff(
    tx: int = 0,
    line: int = 0,
    baseline: str = "PUSH1 (pc=0)",
    current: str = "PUSH1 (pc=1)",
) -> TraceDifference:
    """Create a TraceDifference."""
    return TraceDifference(
        transaction_index=tx,
        trace_line_index=line,
        baseline=baseline,
        current=current,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTextFormatTestResult:
    """Test TextTracesDiffReportFormatter.format_test_result."""

    def test_single_comparator_equivalent(
        self, formatter: TextTracesDiffReportFormatter
    ) -> None:
        """All equivalent returns None."""
        output = formatter.format_test_result(
            "test_foo", {"exact": _make_result(equivalent=True)}
        )
        assert output is None

    def test_single_comparator_with_differences(
        self, formatter: TextTracesDiffReportFormatter
    ) -> None:
        """Single comparator with diffs shows DIFFERENT and details."""
        diffs = [
            _make_diff(
                tx=0,
                line=12,
                baseline="ADD (gas=0x4e20)",
                current="ADD (gas=0x4e10)",
            ),
        ]
        output = formatter.format_test_result(
            "test_bar",
            {"exact": _make_result(equivalent=False, differences=diffs)},
        )
        assert output is not None
        assert "DIFFERENT" in output
        assert "0x4e20" in output
        assert "0x4e10" in output

    def test_multiple_comparators_mixed(
        self, formatter: TextTracesDiffReportFormatter
    ) -> None:
        """Only non-equivalent comparators are shown."""
        diffs = [_make_diff()]
        output = formatter.format_test_result(
            "test_baz",
            {
                "exact": _make_result(equivalent=False, differences=diffs),
                "exact-no-gas": _make_result(equivalent=True),
            },
        )
        assert output is not None
        assert "[exact]" in output
        assert "DIFFERENT" in output
        assert "exact-no-gas" not in output
        assert "EQUIVALENT" not in output

    def test_differences_capped(self) -> None:
        """Only the first max_differences diffs are shown."""
        fmt = TextTracesDiffReportFormatter(max_differences=3)
        diffs = [_make_diff(line=i) for i in range(10)]
        output = fmt.format_test_result(
            "test_cap",
            {"exact": _make_result(equivalent=False, differences=diffs)},
        )
        assert output is not None
        assert "7 more" in output


class TestTextFormatSummary:
    """Test TextTracesDiffReportFormatter.format_summary."""

    def test_no_results(
        self, formatter: TextTracesDiffReportFormatter
    ) -> None:
        """Empty results produce minimal output."""
        output = formatter.format_summary({})
        assert "0 tests verified" in output

    def test_multiple_tests_aggregation(
        self, formatter: TextTracesDiffReportFormatter
    ) -> None:
        """Summary correctly counts tests and those with differences."""
        all_results = {
            "test_a": {"exact": _make_result(equivalent=True)},
            "test_b": {
                "exact": _make_result(
                    equivalent=False,
                    differences=[_make_diff()],
                )
            },
        }
        output = formatter.format_summary(all_results)
        assert "2 tests verified" in output
        assert "1 with differences" in output

    def test_all_equivalent(
        self, formatter: TextTracesDiffReportFormatter
    ) -> None:
        """When all tests pass, only summary line is shown."""
        all_results = {
            "test_a": {"exact": _make_result(equivalent=True)},
            "test_b": {"exact": _make_result(equivalent=True)},
        }
        output = formatter.format_summary(all_results)
        assert "2 tests verified" in output
        assert "0 with differences" in output
        assert "test_a" not in output
        assert "test_b" not in output


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------


class TestJsonTracesDiffReportFormatter:
    """Test JsonTracesDiffReportFormatter.write."""

    def test_writes_json_file(self, tmp_path: pytest.TempPathFactory) -> None:
        """Report is written as valid JSON."""
        out = tmp_path / "report.json"  # type: ignore[operator]
        fmt = JsonTracesDiffReportFormatter(out)
        fmt.write(
            {
                "test_a": {
                    "exact": _make_result(
                        equivalent=False,
                        differences=[_make_diff(tx=0, line=3)],
                    ),
                },
            }
        )
        data = json.loads(out.read_text())
        assert "test_a" in data
        assert data["test_a"]["exact"]["equivalent"] is False
        diffs = data["test_a"]["exact"]["differences"]
        assert len(diffs) == 1
        assert diffs[0]["transaction_index"] == 0
        assert diffs[0]["trace_line_index"] == 3

    def test_equivalent_tests_included(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Equivalent tests are included in JSON (unlike text report)."""
        out = tmp_path / "report.json"  # type: ignore[operator]
        fmt = JsonTracesDiffReportFormatter(out)
        fmt.write(
            {
                "test_a": {"exact": _make_result(equivalent=True)},
            }
        )
        data = json.loads(out.read_text())
        assert data["test_a"]["exact"]["equivalent"] is True
        assert data["test_a"]["exact"]["differences"] == []

    def test_creates_parent_directories(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Parent directories are created if they don't exist."""
        out = tmp_path / "sub" / "dir" / "report.json"  # type: ignore[operator]
        fmt = JsonTracesDiffReportFormatter(out)
        fmt.write({"test_a": {"exact": _make_result(equivalent=True)}})
        assert out.exists()
