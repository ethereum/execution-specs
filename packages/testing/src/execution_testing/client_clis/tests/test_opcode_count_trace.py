"""Test suite for the opcode-count trace request in ``ClientBackend``."""

from typing import Any, Dict, List

import pytest

from execution_testing.base_types import Hash
from execution_testing.client_clis import ClientBackend
from execution_testing.client_clis.client_backend import (
    DEFAULT_OPCODE_COUNT_TRACE_TIMEOUT,
    OPCODE_COUNT_TRACER_JS,
    STRUCT_LOG_TRACER_CONFIG,
)
from execution_testing.rpc.rpc_types import JSONRPCError

BLOCK_HASH = Hash(0)
JS_TRACER_REJECTED = JSONRPCError(code=-32601, message="method not found")
JS_TRACE = [{"result": {"PUSH0": 3}}]
STRUCT_LOG_TRACE = [{"result": {"structLogs": [{"op": "PUSH0"}]}}]


class StubDebugRPC:
    """Record each trace request's config and replay a canned response."""

    def __init__(self, responses: List[Any]) -> None:
        self.responses = responses
        self.configs: List[Dict[str, Any]] = []

    def trace_block_by_hash(
        self, _block_hash: str, tracer_config: Dict[str, Any]
    ) -> Any:
        """Record the request config, then return or raise the response."""
        self.configs.append(tracer_config)
        response = self.responses[len(self.configs) - 1]
        if isinstance(response, Exception):
            raise response
        return response


def _trace_configs(
    responses: List[Any],
    timeout: str = DEFAULT_OPCODE_COUNT_TRACE_TIMEOUT,
) -> List[Dict[str, Any]]:
    """Return the configs ``extract_block_opcode_count`` sends per call."""
    # ``__new__`` skips ``__init__``: the trace path needs no live client.
    backend = ClientBackend.__new__(ClientBackend)
    backend.extract_opcode_count = True
    backend.opcode_count_trace_timeout = timeout
    backend._js_tracer_unsupported = False
    debug_rpc = StubDebugRPC(responses)
    backend.debug_rpc = debug_rpc  # type: ignore[assignment]
    backend.extract_block_opcode_count(BLOCK_HASH)
    return debug_rpc.configs


@pytest.mark.parametrize(
    "responses,traced_call,tracer_config",
    [
        pytest.param(
            [JS_TRACE],
            0,
            {"tracer": OPCODE_COUNT_TRACER_JS},
            id="js_tracer",
        ),
        pytest.param(
            [JS_TRACER_REJECTED, STRUCT_LOG_TRACE],
            1,
            STRUCT_LOG_TRACER_CONFIG,
            id="struct_log_fallback",
        ),
    ],
)
def test_trace_request_carries_the_timeout(
    responses: List[Any],
    traced_call: int,
    tracer_config: Dict[str, Any],
) -> None:
    """
    Both tracer paths bound the trace and keep their own config intact.
    """
    configs = _trace_configs(responses)

    config = configs[traced_call]
    assert config["timeout"] == DEFAULT_OPCODE_COUNT_TRACE_TIMEOUT
    for key, value in tracer_config.items():
        assert config[key] == value
