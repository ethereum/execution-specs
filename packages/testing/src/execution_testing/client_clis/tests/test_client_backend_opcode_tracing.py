"""Tests for ClientBackend opcode-trace collection."""

from typing import Any, Dict

import pytest

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    Hash,
    HexNumber,
)
from execution_testing.client_clis.cli_types import OpcodeCount
from execution_testing.client_clis.client_backend import ClientBackend
from execution_testing.client_clis.transition_tool import TransitionTool
from execution_testing.fixtures.blockchain import FixtureExecutionPayload
from execution_testing.forks import Prague
from execution_testing.rpc.rpc_types import GetPayloadResponse
from execution_testing.test_types import Alloc, Environment


class TracerStub:
    """Stand-in for DebugRPC.trace_block_opcode_counts."""

    def __init__(self, counts: Dict[str, int] | None) -> None:
        """Return the given counts for every traced block."""
        self.counts = counts
        self.traced_blocks: list[str] = []

    def trace_block_opcode_counts(
        self, block_number: str
    ) -> Dict[str, int] | None:
        """Record the request and return the configured counts."""
        self.traced_blocks.append(block_number)
        return self.counts


class RaisingTracerStub:
    """Tracer stand-in whose trace call always raises."""

    def trace_block_opcode_counts(self, block_number: str) -> None:
        """Raise to simulate a client-side trace failure."""
        del block_number
        raise RuntimeError("trace exploded")


@pytest.fixture
def backend(monkeypatch: pytest.MonkeyPatch) -> ClientBackend:
    """ClientBackend with stubbed RPC dependencies (no network)."""

    class Web3Stub:
        def __init__(self, url: str) -> None:
            pass

        def client_version(self) -> str:
            return "stub/v0.0.0"

    monkeypatch.setattr(
        "execution_testing.client_clis.client_backend.Web3RPC", Web3Stub
    )

    class EthRPCStub:
        url = "http://localhost:8545"

    return ClientBackend(
        testing_rpc=None,  # type: ignore[arg-type]
        engine_rpc=None,  # type: ignore[arg-type]
        eth_rpc=EthRPCStub(),  # type: ignore[arg-type]
        fork=Prague,
    )


def test_trace_disabled_by_default(backend: ClientBackend) -> None:
    """No tracer RPC is attached unless the plugin sets one."""
    assert backend.opcode_tracer_rpc is None


def test_trace_block_opcode_count(backend: ClientBackend) -> None:
    """Return validated OpcodeCount from the tracer's raw counts."""
    tracer = TracerStub({"PUSH1": 2, "SLOAD": 1})
    backend.opcode_tracer_rpc = tracer  # type: ignore[assignment]
    opcode_count = backend._trace_block_opcode_count(5)
    assert opcode_count is not None
    assert opcode_count.model_dump() == {"PUSH1": 2, "SLOAD": 1}
    assert tracer.traced_blocks == ["0x5"]


def test_trace_block_unsupported_client(backend: ClientBackend) -> None:
    """Propagate None when the tracer reports no support."""
    backend.opcode_tracer_rpc = TracerStub(None)  # type: ignore[assignment]
    assert backend._trace_block_opcode_count(5) is None


def test_trace_block_failure_is_non_fatal(
    backend: ClientBackend, caplog: pytest.LogCaptureFixture
) -> None:
    """A trace error yields None with a warning; the fill continues."""
    backend.opcode_tracer_rpc = RaisingTracerStub()  # type: ignore[assignment]
    with caplog.at_level("WARNING"):
        assert backend._trace_block_opcode_count(5) is None
    assert any("trace" in r.message.lower() for r in caplog.records)


def test_trace_block_unknown_opcode_name(
    backend: ClientBackend, caplog: pytest.LogCaptureFixture
) -> None:
    """Unparsable opcode names yield None instead of failing the fill."""
    backend.opcode_tracer_rpc = TracerStub(  # type: ignore[assignment]
        {"NOT_AN_OPCODE": 1}
    )
    with caplog.at_level("WARNING"):
        assert backend._trace_block_opcode_count(5) is None
    assert any("opcode" in r.message.lower() for r in caplog.records)


def test_record_requires_test_id(backend: ClientBackend) -> None:
    """Recording without a current test id is a no-op."""
    backend.record_test_opcode_count(OpcodeCount.model_validate({"PUSH1": 1}))
    assert backend.collected_opcode_counts == {}


def test_record_and_merge(backend: ClientBackend) -> None:
    """Repeated records for the same test are summed."""
    backend.current_test_id = "tests/test_mod.py::test_case[x]"
    backend.record_test_opcode_count(
        OpcodeCount.model_validate({"PUSH1": 1, "ADD": 2})
    )
    backend.record_test_opcode_count(OpcodeCount.model_validate({"PUSH1": 3}))
    recorded = backend.collected_opcode_counts[
        "tests/test_mod.py::test_case[x]"
    ]
    assert recorded.model_dump() == {"PUSH1": 4, "ADD": 2}


def test_record_separate_tests(backend: ClientBackend) -> None:
    """Counts land under the test id active at record time."""
    backend.current_test_id = "tests/test_mod.py::test_one"
    backend.record_test_opcode_count(OpcodeCount.model_validate({"PUSH1": 1}))
    backend.current_test_id = "tests/test_mod.py::test_two"
    backend.record_test_opcode_count(OpcodeCount.model_validate({"ADD": 1}))
    assert set(backend.collected_opcode_counts) == {
        "tests/test_mod.py::test_one",
        "tests/test_mod.py::test_two",
    }


def _evaluate_with_stub_client(backend: ClientBackend) -> Any:
    """
    Run ``evaluate`` against a stubbed client.

    ``build_block`` returns a canned empty payload and the engine
    finalization is skipped; everything else (result assembly and the
    opcode-trace hook) runs for real.
    """
    payload = FixtureExecutionPayload(
        parent_hash=Hash(0),
        fee_recipient=Address(0),
        state_root=Hash(0),
        receipts_root=Hash(0),
        logs_bloom=Bloom(b"\x00" * 256),
        number=HexNumber(7),
        gas_limit=HexNumber(30_000_000),
        gas_used=HexNumber(0),
        timestamp=HexNumber(0),
        extra_data=Bytes(b""),
        prev_randao=Hash(0),
        base_fee_per_gas=HexNumber(7),
        blob_gas_used=HexNumber(0),
        excess_blob_gas=HexNumber(0),
        block_hash=Hash(1),
        transactions=[],
        withdrawals=[],
    )

    class TestingRPCStub:
        @staticmethod
        def build_block(**kwargs: Any) -> GetPayloadResponse:
            del kwargs
            return GetPayloadResponse(
                execution_payload=payload, execution_requests=[]
            )

    def skip_finalize(*args: Any, **kwargs: Any) -> None:
        del args, kwargs

    backend.testing_rpc = TestingRPCStub()  # type: ignore[assignment]
    backend._finalize = skip_finalize  # type: ignore[method-assign]
    transition_tool_data = TransitionTool.TransitionToolData(
        alloc=Alloc(),
        txs=[],
        env=Environment(withdrawals=[]),
        fork=Prague,
        chain_id=1,
        reward=0,
        blob_schedule=None,
    )
    return backend.evaluate(transition_tool_data=transition_tool_data)


def test_evaluate_without_tracing(backend: ClientBackend) -> None:
    """Evaluate leaves opcode_count unset when tracing is disabled."""
    output = _evaluate_with_stub_client(backend)
    assert output.result.opcode_count is None


def test_evaluate_with_tracing(backend: ClientBackend) -> None:
    """Evaluate traces the built block when a tracer RPC is attached."""
    tracer = TracerStub({"STOP": 1})
    backend.opcode_tracer_rpc = tracer  # type: ignore[assignment]
    output = _evaluate_with_stub_client(backend)
    assert output.result.opcode_count is not None
    assert output.result.opcode_count.model_dump() == {"STOP": 1}
    assert tracer.traced_blocks == ["0x7"]
