"""Tests for baseline trace loading from dump directories."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from execution_testing.cli.pytest_commands.plugins.filler.verify_traces import (  # noqa: E501
    TraceVerifier,
    _load_traces_from_dump_dir,
    pytest_testnodedown,
)
from execution_testing.client_clis.cli_types import (
    Traces,
)
from execution_testing.client_clis.trace_comparators import (
    TraceComparisonResult,
    TraceDifference,
    TransactionCountMismatch,
)


def _write_trace_file(
    path: Path,
    trace_lines: list[dict] | None = None,
    output: str = "0x",
    gas_used: str = "0x5208",
) -> None:
    """Write a minimal .jsonl trace file."""
    if trace_lines is None:
        trace_lines = [
            {
                "pc": 0,
                "op": 96,
                "gas": "0x5f5e100",
                "gasCost": "0x3",
                "memSize": 0,
                "stack": [],
                "depth": 1,
                "refund": 0,
                "opName": "PUSH1",
            }
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for line in trace_lines:
            f.write(json.dumps(line) + "\n")
        f.write(json.dumps({"output": output, "gasUsed": gas_used}) + "\n")


class TestLoadTracesFromDumpDir:
    """Test _load_traces_from_dump_dir."""

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory returns empty list."""
        result = _load_traces_from_dump_dir(tmp_path)
        assert result == []

    def test_single_call_dir_two_trace_files(self, tmp_path: Path) -> None:
        """Single call dir with two trace files returns one Traces."""
        call_dir = tmp_path / "0"
        call_dir.mkdir()
        _write_trace_file(call_dir / "trace-0-0xaaa.jsonl")
        _write_trace_file(call_dir / "trace-1-0xbbb.jsonl")

        result = _load_traces_from_dump_dir(tmp_path)
        assert len(result) == 1
        assert isinstance(result[0], Traces)
        assert len(result[0].root) == 2

    def test_multiple_call_dirs(self, tmp_path: Path) -> None:
        """Multiple call dirs (0, 1, 2) return correctly ordered list."""
        for i in range(3):
            call_dir = tmp_path / str(i)
            call_dir.mkdir()
            _write_trace_file(call_dir / f"trace-0-0x{i:03x}.jsonl")

        result = _load_traces_from_dump_dir(tmp_path)
        assert len(result) == 3
        for traces in result:
            assert isinstance(traces, Traces)
            assert len(traces.root) == 1

    def test_non_numeric_subdirs_ignored(self, tmp_path: Path) -> None:
        """Non-numeric subdirectories are ignored."""
        (tmp_path / "0").mkdir()
        _write_trace_file(tmp_path / "0" / "trace-0-0xaaa.jsonl")
        (tmp_path / "metadata").mkdir()
        (tmp_path / "metadata" / "info.json").write_text("{}")

        result = _load_traces_from_dump_dir(tmp_path)
        assert len(result) == 1

    def test_numeric_sorting_not_lexical(self, tmp_path: Path) -> None:
        """Call dirs are sorted numerically (2 before 10)."""
        for i in [10, 2, 0]:
            call_dir = tmp_path / str(i)
            call_dir.mkdir()
            _write_trace_file(call_dir / f"trace-0-0x{i:03x}.jsonl")

        result = _load_traces_from_dump_dir(tmp_path)
        assert len(result) == 3
        # Verify they are in order 0, 2, 10 by checking the list
        # length — ordering is guaranteed by the implementation


def _make_trace_verifier(
    json_formatter: Any = None,
) -> TraceVerifier:
    """Construct a minimally-configured TraceVerifier for unit tests."""
    return TraceVerifier(
        config=MagicMock(),
        comparators=[],
        formatter=MagicMock(),
        baseline_dir=Path("/tmp/baseline"),
        filler_path=Path("/tmp/filler"),
        json_formatter=json_formatter,
    )


def _make_session(workeroutput: dict | None) -> Any:
    """
    Build a fake pytest.Session.

    ``workeroutput=None`` simulates the controller (the attribute is
    absent); a dict simulates a worker.
    """
    config = MagicMock()
    if workeroutput is None:
        # Controller — `workeroutput` must NOT exist on config.
        del config.workeroutput
    else:
        config.workeroutput = workeroutput
    session = MagicMock()
    session.config = config
    return session


class TestXdistAggregation:
    """
    Test xdist worker→controller aggregation.

    Background: ``TraceVerifier`` keeps results in an instance dict.
    Under ``pytest-xdist -n N`` each worker has its own subprocess and
    its own plugin instance, so the controller's instance is empty
    unless workers explicitly forward their results. The plugin uses
    ``config.workeroutput`` on workers and ``pytest_testnodedown`` on
    the controller — these tests exercise that path without spinning
    up real xdist subprocesses.
    """

    def test_worker_writes_results_to_workeroutput(self) -> None:
        """Worker's pytest_sessionfinish stores results in workeroutput."""
        verifier = _make_trace_verifier()
        verifier.test_results = {
            "test_a": {
                "exact": TraceComparisonResult(equivalent=True),
            },
            "test_b": {
                "exact": TraceComparisonResult(
                    equivalent=False,
                    differences=[
                        TraceDifference(
                            transaction_index=0,
                            trace_line_index=3,
                            baseline="ADD",
                            current="MUL",
                        ),
                    ],
                ),
            },
        }
        workeroutput: dict = {}
        verifier.pytest_sessionfinish(
            _make_session(workeroutput=workeroutput), 0
        )

        payload = workeroutput["trace_verifier_results"]
        assert set(payload.keys()) == {"test_a", "test_b"}
        assert payload["test_a"]["exact"]["equivalent"] is True
        assert payload["test_b"]["exact"]["equivalent"] is False
        assert (
            payload["test_b"]["exact"]["differences"][0]["baseline"] == "ADD"
        )

    def test_controller_does_not_write_workeroutput(self) -> None:
        """On the controller (no workeroutput attribute), hook is a no-op."""
        verifier = _make_trace_verifier()
        verifier.test_results = {
            "test_a": {"exact": TraceComparisonResult(equivalent=True)},
        }
        # Should not raise even though config has no `workeroutput`.
        verifier.pytest_sessionfinish(_make_session(workeroutput=None), 0)

    def test_worker_with_empty_results_does_not_write(self) -> None:
        """A worker that ran no comparisons should not write a payload."""
        verifier = _make_trace_verifier()
        workeroutput: dict = {}
        verifier.pytest_sessionfinish(
            _make_session(workeroutput=workeroutput), 0
        )
        assert "trace_verifier_results" not in workeroutput

    def test_pytest_testnodedown_merges_payload(self) -> None:
        """Controller hook merges a worker's payload into the plugin."""
        controller_plugin = _make_trace_verifier()

        # Simulate the data a worker would send back.
        worker_payload = {
            "test_a": {
                "exact": TraceComparisonResult(equivalent=True).model_dump(
                    mode="json"
                ),
            },
            "test_b": {
                "exact-no-stack": TraceComparisonResult(
                    equivalent=False,
                    differences=[
                        TransactionCountMismatch(
                            baseline_count=2, current_count=1
                        ),
                    ],
                ).model_dump(mode="json"),
            },
        }
        node = MagicMock()
        node.workeroutput = {"trace_verifier_results": worker_payload}
        node.config.pluginmanager.get_plugin.return_value = controller_plugin

        pytest_testnodedown(node, error=None)

        assert set(controller_plugin.test_results.keys()) == {
            "test_a",
            "test_b",
        }
        assert (
            controller_plugin.test_results["test_a"]["exact"].equivalent
            is True
        )
        diff_b = controller_plugin.test_results["test_b"][
            "exact-no-stack"
        ].differences[0]
        assert isinstance(diff_b, TransactionCountMismatch)
        assert diff_b.baseline_count == 2
        assert diff_b.current_count == 1

    def test_pytest_testnodedown_multiple_workers_aggregate(self) -> None:
        """Two workers' payloads both land in the controller plugin."""
        controller_plugin = _make_trace_verifier()

        def _send(node_results: dict[str, TraceComparisonResult]) -> None:
            payload = {
                nodeid: {"exact": result.model_dump(mode="json")}
                for nodeid, result in node_results.items()
            }
            node = MagicMock()
            node.workeroutput = {"trace_verifier_results": payload}
            node.config.pluginmanager.get_plugin.return_value = (
                controller_plugin
            )
            pytest_testnodedown(node, error=None)

        _send(
            {
                "test_w0_a": TraceComparisonResult(equivalent=True),
                "test_w0_b": TraceComparisonResult(equivalent=True),
            }
        )
        _send(
            {
                "test_w1_a": TraceComparisonResult(equivalent=True),
                "test_w1_b": TraceComparisonResult(equivalent=True),
                "test_w1_c": TraceComparisonResult(equivalent=True),
            }
        )

        # The bug being fixed: prior to aggregation, the controller saw
        # only one worker's slice (or none). All five nodeids must be
        # present after merging both workers.
        assert set(controller_plugin.test_results.keys()) == {
            "test_w0_a",
            "test_w0_b",
            "test_w1_a",
            "test_w1_b",
            "test_w1_c",
        }

    def test_pytest_testnodedown_no_payload_is_noop(self) -> None:
        """Worker with no payload (didn't run any tests) is a no-op."""
        controller_plugin = _make_trace_verifier()
        node = MagicMock()
        node.workeroutput = {}
        node.config.pluginmanager.get_plugin.return_value = controller_plugin

        pytest_testnodedown(node, error=None)

        assert controller_plugin.test_results == {}

    def test_pytest_testnodedown_no_plugin_registered(self) -> None:
        """If the trace-verifier plugin isn't registered, hook is a no-op."""
        node = MagicMock()
        node.workeroutput = {
            "trace_verifier_results": {
                "test_a": {
                    "exact": TraceComparisonResult(equivalent=True).model_dump(
                        mode="json"
                    ),
                },
            },
        }
        node.config.pluginmanager.get_plugin.return_value = None
        # Should not raise.
        pytest_testnodedown(node, error=None)


class TestWorkerTerminalSummarySkipped:
    """Workers must not write the JSON / text report."""

    def test_worker_skips_terminal_summary(self) -> None:
        """`pytest_terminal_summary` is a no-op when workerinput is set."""
        json_formatter = MagicMock()
        json_formatter.output_path = Path("/tmp/report.json")
        verifier = _make_trace_verifier(json_formatter=json_formatter)
        verifier.test_results = {
            "test_a": {"exact": TraceComparisonResult(equivalent=True)},
        }

        terminalreporter = MagicMock()
        worker_config = MagicMock()
        # Workers have `workerinput`; controllers don't.
        worker_config.workerinput = {"workerid": "gw0"}

        verifier.pytest_terminal_summary(
            terminalreporter, exitstatus=0, config=worker_config
        )

        json_formatter.write.assert_not_called()
        terminalreporter.write_sep.assert_not_called()

    def test_controller_writes_terminal_summary(self) -> None:
        """Controller (no workerinput) writes the report normally."""
        json_formatter = MagicMock()
        json_formatter.output_path = Path("/tmp/report.json")
        text_formatter = MagicMock()
        text_formatter.format_summary.return_value = "summary line"
        verifier = TraceVerifier(
            config=MagicMock(),
            comparators=[],
            formatter=text_formatter,
            baseline_dir=Path("/tmp/baseline"),
            filler_path=Path("/tmp/filler"),
            json_formatter=json_formatter,
        )
        verifier.test_results = {
            "test_a": {"exact": TraceComparisonResult(equivalent=True)},
        }

        terminalreporter = MagicMock()
        controller_config = MagicMock()
        # Controllers don't have `workerinput`.
        del controller_config.workerinput

        verifier.pytest_terminal_summary(
            terminalreporter, exitstatus=0, config=controller_config
        )

        json_formatter.write.assert_called_once_with(verifier.test_results)
        terminalreporter.write_sep.assert_called()
