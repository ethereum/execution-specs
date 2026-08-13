"""Test suite for the opcode-count trace request in ``ClientBackend``."""

from typing import Any, Dict, List, Tuple

from execution_testing.base_types import Hash
from execution_testing.client_clis import ClientBackend
from execution_testing.client_clis.client_backend import (
    OPCODE_COUNT_TRACE_TIMEOUT,
    OPCODE_COUNT_TRACER_JS,
    STRUCT_LOG_TRACER_CONFIG,
)
from execution_testing.rpc.rpc_types import JSONRPCError

BLOCK_HASH = Hash(0)


class StubDebugRPC:
    """
    Records the ``debug_traceBlockByHash`` config it is called with and
    replays a canned response per call.
    """

    def __init__(self, responses: List[Any]) -> None:
        self.responses = responses
        self.calls: List[Tuple[str, Dict[str, Any]]] = []

    def trace_block_by_hash(
        self, block_hash: str, tracer_config: Dict[str, Any]
    ) -> Any:
        """Record the request, then return or raise the canned response."""
        self.calls.append((block_hash, tracer_config))
        response = self.responses[len(self.calls) - 1]
        if isinstance(response, Exception):
            raise response
        return response


def _backend(responses: List[Any]) -> ClientBackend:
    """
    Stub ``ClientBackend`` wired to ``StubDebugRPC``.

    ``__new__`` skips ``__init__``: the trace path needs no live client.
    """
    backend = ClientBackend.__new__(ClientBackend)
    backend.extract_opcode_count = True
    backend._js_tracer_unsupported = False
    backend.debug_rpc = StubDebugRPC(responses)  # type: ignore[assignment]
    return backend


def test_js_tracer_request_carries_a_timeout() -> None:
    """
    The JS-tracer request must set ``timeout``.

    A client's own default bounds each transaction's trace (5s on geth) and
    abandons it when that expires. A benchmark block outruns it, and the
    abandoned transaction contributes no counts, so the tally is silently
    short rather than absent.
    """
    backend = _backend([[{"result": {"PUSH0": 3}}]])

    backend.extract_block_opcode_count(BLOCK_HASH)

    _, config = backend.debug_rpc.calls[0]  # type: ignore[union-attr]
    assert config["timeout"] == OPCODE_COUNT_TRACE_TIMEOUT
    assert config["tracer"] == OPCODE_COUNT_TRACER_JS


def test_struct_log_fallback_request_carries_a_timeout() -> None:
    """The struct-log fallback is bounded the same way, and stays intact."""
    backend = _backend(
        [
            JSONRPCError(code=-32601, message="method not found"),
            [{"result": {"structLogs": [{"op": "PUSH0"}]}}],
        ]
    )

    backend.extract_block_opcode_count(BLOCK_HASH)

    _, config = backend.debug_rpc.calls[1]  # type: ignore[union-attr]
    assert config["timeout"] == OPCODE_COUNT_TRACE_TIMEOUT
    for key, value in STRUCT_LOG_TRACER_CONFIG.items():
        assert config[key] == value


def test_timeout_is_a_duration_the_client_can_parse() -> None:
    """
    The value reaches the client verbatim, so it has to be a Go duration
    string -- a bare number is rejected.
    """
    assert isinstance(OPCODE_COUNT_TRACE_TIMEOUT, str)
    assert OPCODE_COUNT_TRACE_TIMEOUT[-1] in "smh"
    assert float(OPCODE_COUNT_TRACE_TIMEOUT[:-1]) > 0
