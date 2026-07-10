"""Tests for DebugRPC opcode tracing (unigram tracer + fallback)."""

from typing import Any, Dict, List, Tuple

import pytest

from execution_testing.rpc.rpc import DebugRPC, sum_unigram_block_trace
from execution_testing.rpc.rpc_types import JSONRPCError

# ---------------------------------------------------------------------------
# sum_unigram_block_trace
# ---------------------------------------------------------------------------


def test_sum_geth_shape() -> None:
    """Sum per-transaction entries with txHash + result (geth)."""
    block_trace = [
        {"txHash": "0x1", "result": {"PUSH1": 2, "ADD": 1}},
        {"txHash": "0x2", "result": {"PUSH1": 3, "SLOAD": 4}},
    ]
    assert sum_unigram_block_trace(block_trace) == {
        "PUSH1": 5,
        "ADD": 1,
        "SLOAD": 4,
    }


def test_sum_legacy_shape() -> None:
    """Sum entries without txHash (older geth/erigon)."""
    block_trace = [
        {"result": {"PUSH1": 1}},
        {"result": {"PUSH1": 1}},
    ]
    assert sum_unigram_block_trace(block_trace) == {"PUSH1": 2}


def test_sum_bare_map_shape() -> None:
    """Sum entries that are bare opcode maps."""
    block_trace = [{"PUSH1": 1, "STOP": 1}]
    assert sum_unigram_block_trace(block_trace) == {"PUSH1": 1, "STOP": 1}


def test_sum_skips_error_entries() -> None:
    """Skip per-transaction error entries and non-integer values."""
    block_trace = [
        {"txHash": "0x1", "error": "execution aborted"},
        {"result": {"PUSH1": 1}},
        {"result": "not a dict"},
        "not a dict either",
    ]
    assert sum_unigram_block_trace(block_trace) == {"PUSH1": 1}


def test_sum_empty_block() -> None:
    """Return an empty count for a block with no transactions."""
    assert sum_unigram_block_trace([]) == {}


def test_sum_non_list_input() -> None:
    """Return an empty count for unexpected response shapes."""
    assert sum_unigram_block_trace(None) == {}
    assert sum_unigram_block_trace({"PUSH1": 1}) == {}


# ---------------------------------------------------------------------------
# DebugRPC.trace_block_opcode_counts fallback behavior
# ---------------------------------------------------------------------------


class TracerRecorder:
    """Patched trace_block_by_number recording calls per tracer."""

    def __init__(self, rejected_tracers: set[str]) -> None:
        """Reject the given tracers; accept all others."""
        self.rejected_tracers = rejected_tracers
        self.calls: List[Tuple[str, str]] = []

    def __call__(self, block_number: str, tracer: str) -> Any:
        """Simulate the client's tracer support."""
        self.calls.append((block_number, tracer))
        if tracer in self.rejected_tracers:
            raise JSONRPCError(code=-32602, message="tracer not found")
        return [{"txHash": "0x1", "result": {"PUSH1": 2, "ADD": 1}}]


@pytest.fixture
def debug_rpc() -> DebugRPC:
    """DebugRPC instance; no requests are made (methods are patched)."""
    return DebugRPC("http://localhost:8545")


def test_tracer_by_name(
    debug_rpc: DebugRPC, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use the built-in unigramTracer name when the client accepts it."""
    recorder = TracerRecorder(rejected_tracers=set())
    monkeypatch.setattr(debug_rpc, "trace_block_by_number", recorder)

    counts = debug_rpc.trace_block_opcode_counts("0x2")
    assert counts == {"PUSH1": 2, "ADD": 1}
    assert recorder.calls == [("0x2", "unigramTracer")]

    # Cached: the second call goes straight to the name, no re-probe.
    debug_rpc.trace_block_opcode_counts("0x3")
    assert recorder.calls[1:] == [("0x3", "unigramTracer")]


def test_tracer_js_fallback(
    debug_rpc: DebugRPC, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fall back to the inline JS tracer when the name is rejected."""
    recorder = TracerRecorder(rejected_tracers={"unigramTracer"})
    monkeypatch.setattr(debug_rpc, "trace_block_by_number", recorder)

    counts = debug_rpc.trace_block_opcode_counts("0x2")
    assert counts == {"PUSH1": 2, "ADD": 1}
    assert recorder.calls == [
        ("0x2", "unigramTracer"),
        ("0x2", DebugRPC.UNIGRAM_TRACER_JS),
    ]

    # Cached: no name re-probe on subsequent calls.
    debug_rpc.trace_block_opcode_counts("0x3")
    assert recorder.calls[2:] == [("0x3", DebugRPC.UNIGRAM_TRACER_JS)]


def test_tracer_unsupported(
    debug_rpc: DebugRPC,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Warn once and return None when the client supports no tracer."""
    recorder = TracerRecorder(
        rejected_tracers={"unigramTracer", DebugRPC.UNIGRAM_TRACER_JS}
    )
    monkeypatch.setattr(debug_rpc, "trace_block_by_number", recorder)

    with caplog.at_level("WARNING"):
        assert debug_rpc.trace_block_opcode_counts("0x2") is None
    assert len(recorder.calls) == 2
    assert any("opcode" in record.message.lower() for record in caplog.records)

    # Cached: subsequent calls return None without any RPC traffic.
    assert debug_rpc.trace_block_opcode_counts("0x3") is None
    assert len(recorder.calls) == 2


def test_trace_block_by_number_request_shape(
    debug_rpc: DebugRPC, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Post debug_traceBlockByNumber with [block, {tracer}] params."""
    captured: Dict[str, Any] = {}

    def fake_post_request(*, request: Any, **kwargs: Any) -> Any:
        del kwargs
        captured["method"] = request.method
        captured["params"] = request.params

        class Response:
            @staticmethod
            def result_or_raise() -> Any:
                return []

        return Response()

    monkeypatch.setattr(debug_rpc, "post_request", fake_post_request)
    debug_rpc.trace_block_by_number("0x2", "unigramTracer")
    assert captured["method"] == "traceBlockByNumber"
    assert captured["params"] == ["0x2", {"tracer": "unigramTracer"}]
