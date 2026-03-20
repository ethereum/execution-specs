"""Pytest plugin for trace verification against a baseline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generator

import pytest
from _pytest.terminal import TerminalReporter

from execution_testing.cli.pytest_commands.plugins.filler.filler import (
    node_to_test_info,
)
from execution_testing.client_clis.cli_types import (
    Traces,
    TransactionTraces,
)
from execution_testing.client_clis.trace_comparators import (
    TraceComparator,
    TraceComparatorType,
    TraceComparisonResult,
    create_comparator,
)
from execution_testing.client_clis.trace_report_formatter import (
    TextTracesDiffReportFormatter,
    TracesDiffReportFormatter,
)

# ---------------------------------------------------------------------------
# Baseline loading
# ---------------------------------------------------------------------------


def _load_traces_from_dump_dir(dump_dir: Path) -> list[Traces]:
    """Load traces from numbered call subdirectories."""
    traces_list: list[Traces] = []
    call_dirs = sorted(
        (d for d in dump_dir.iterdir() if d.is_dir() and d.name.isdigit()),
        key=lambda d: int(d.name),
    )
    for call_dir in call_dirs:
        traces = Traces(root=[])
        trace_files = sorted(call_dir.glob("trace-*.jsonl"))
        for trace_file in trace_files:
            traces.append(TransactionTraces.from_file(trace_file))
        traces_list.append(traces)
    return traces_list


# ---------------------------------------------------------------------------
# CLI flags
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register --verify-traces and --verify-traces-comparator."""
    group = parser.getgroup("verify_traces", "Trace verification options")
    group.addoption(
        "--verify-traces",
        action="store",
        dest="verify_traces_dir",
        type=Path,
        default=None,
        help=(
            "Baseline trace dump directory. "
            "Compares current traces against baseline. "
            "Implies --traces."
        ),
    )
    group.addoption(
        "--verify-traces-comparator",
        action="store",
        dest="verify_traces_comparator",
        type=str,
        default="exact-no-gas",
        help=(
            "Comma-separated comparator names. "
            "Choices: exact, exact-no-gas. "
            "Default: exact-no-gas."
        ),
    )


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Register the TraceVerifier plugin if --verify-traces is set."""
    verify_traces_dir = config.getoption("verify_traces_dir", None)
    if verify_traces_dir is None:
        return

    config.collect_traces = True  # type: ignore[attr-defined]
    config.option.evm_collect_traces = True

    comparator_names = config.getoption("verify_traces_comparator").split(",")
    comparators = [
        create_comparator(TraceComparatorType(name.strip()))
        for name in comparator_names
    ]

    formatter = TextTracesDiffReportFormatter()

    filler_path = Path(config.getoption("filler_path"))

    config.pluginmanager.register(
        TraceVerifier(
            config=config,
            comparators=comparators,
            formatter=formatter,
            baseline_dir=Path(verify_traces_dir),
            filler_path=filler_path,
        ),
        "trace-verifier",
    )


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------


class TraceVerifier:
    """Pytest plugin for trace verification against a baseline."""

    def __init__(
        self,
        config: pytest.Config,
        comparators: list[TraceComparator],
        formatter: TracesDiffReportFormatter,
        baseline_dir: Path,
        filler_path: Path,
    ) -> None:
        """Initialize with comparators, formatter, and baseline path."""
        self.config = config
        self.comparators = comparators
        self.formatter = formatter
        self.baseline_dir = baseline_dir
        self.filler_path = filler_path
        self.test_results: dict[str, dict[str, TraceComparisonResult]] = {}

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(
        self, item: pytest.Item, call: pytest.CallInfo[None]
    ) -> Generator[None, Any, None]:
        """Collect trace diffs after each test's call phase."""
        outcome = yield
        report = outcome.get_result()

        if call.when != "call" or report.failed:
            return

        t8n = getattr(item.config, "t8n", None)
        if t8n is None:
            return

        current_traces_list = t8n.get_traces()
        if current_traces_list is None:
            return

        test_info = node_to_test_info(item)
        baseline_dump_dir = test_info.get_dump_dir_path(
            self.baseline_dir,
            self.filler_path,
            level="test_parameter",
        )
        if baseline_dump_dir is None or not baseline_dump_dir.exists():
            return

        baseline_traces_list = _load_traces_from_dump_dir(baseline_dump_dir)

        if not current_traces_list:
            return  # No traces collected (e.g. t8n cache hit)

        # Compare each pair of Traces objects (one per t8n call)
        results: dict[str, TraceComparisonResult] = {}
        for comparator in self.comparators:
            all_diffs = []
            all_equivalent = True
            for baseline, current in zip(
                baseline_traces_list, current_traces_list, strict=False
            ):
                result = comparator.compare_traces(baseline, current)
                all_diffs.extend(result.differences)
                if not result.equivalent:
                    all_equivalent = False
            results[comparator.name] = TraceComparisonResult(
                equivalent=all_equivalent,
                differences=all_diffs,
            )

        if results:
            self.test_results[item.nodeid] = results

    def pytest_terminal_summary(
        self,
        terminalreporter: TerminalReporter,
        exitstatus: int,  # noqa: ARG002
        config: pytest.Config,  # noqa: ARG002
    ) -> None:
        """Print the aggregated trace verification report."""
        if not self.test_results:
            return

        output = self.formatter.format_summary(self.test_results)
        terminalreporter.write_sep("=", "trace verification report")
        for line in output.splitlines():
            terminalreporter.write_line(line)
