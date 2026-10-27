"""Exercise synchronous inclusion verdicts and execution-sync retries."""

from typing import Any
from unittest.mock import Mock

import pytest

from execution_testing.base_types import Hash
from execution_testing.rpc.rpc import EngineRPC
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    JSONRPCError,
    PayloadStatus,
    PayloadStatusEnum,
)


def status(
    verdict: bool | None = None, *, syncing: bool = False
) -> PayloadStatus:
    """Return execution and inclusion statuses for one execution block."""
    return PayloadStatus(
        status=PayloadStatusEnum.SYNCING
        if syncing
        else PayloadStatusEnum.VALID,
        latest_valid_hash=None if syncing else Hash(1),
        validation_error=None,
        inclusion_list_satisfied=verdict,
    )


@pytest.mark.parametrize("verdict", [True, False])
@pytest.mark.parametrize("syncing", [True, False])
def test_completed_verdict(verdict: bool, syncing: bool) -> None:
    """Retry only incomplete execution, preserving duplicate ILs and claims."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.new_payload = Mock(return_value=status(verdict))
    claim = {"transactionHash": Hash(4), "evaluationIndex": "0x2"}
    inputs: tuple[Any, ...] = (
        {"blockHash": Hash(1)},
        [],
        Hash(0),
        [],
        [["0xc0", "0xc0"]] + [[]] * 15,
        [claim, claim],
    )
    initial = status(syncing=True) if syncing else status(verdict)
    result = rpc.wait_for_inclusion_list(
        initial, *inputs, version=6, wait_fixed=0
    )
    assert result.inclusion_list_satisfied is verdict
    assert rpc.new_payload.call_count == int(syncing)
    for call in rpc.new_payload.call_args_list:
        assert call.args == inputs
        assert call.kwargs == {"version": 6}


def test_incomplete_execution_times_out() -> None:
    """Do not treat a perpetually syncing payload as satisfied."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.new_payload = Mock(return_value=status(syncing=True))
    with pytest.raises(TimeoutError, match="remained pending"):
        rpc.wait_for_inclusion_list(
            status(syncing=True), version=6, max_attempts=2, wait_fixed=0
        )
    assert rpc.new_payload.call_count == 2


def test_retry_does_not_swallow_rpc_errors() -> None:
    """Propagate an RPC error instead of mistaking it for satisfaction."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.new_payload = Mock(side_effect=JSONRPCError(-32603, "Internal error"))
    with pytest.raises(JSONRPCError, match="Internal error"):
        rpc.wait_for_inclusion_list(
            status(syncing=True), version=6, wait_fixed=0
        )


def test_invalid_execution_needs_no_inclusion_verdict() -> None:
    """Stop retrying when execution itself is invalid."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.new_payload = Mock()
    invalid = status().model_copy(update={"status": PayloadStatusEnum.INVALID})
    assert rpc.wait_for_inclusion_list(invalid, version=6) is invalid
    rpc.new_payload.assert_not_called()


def test_inclusion_verdict_requires_valid_execution() -> None:
    """Reject a premature inclusion verdict from a still-syncing payload."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    with pytest.raises(ValueError, match="precedes valid execution"):
        rpc.wait_for_inclusion_list(status(True, syncing=True), version=6)


def test_valid_response_requires_inclusion_verdict() -> None:
    """Reject VALID with a missing verdict instead of polling for one."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.new_payload = Mock()
    with pytest.raises(ValueError, match="lacks inclusion verdict"):
        rpc.wait_for_inclusion_list(status(), version=6)
    rpc.new_payload.assert_not_called()


@pytest.mark.parametrize("custody", [None, b"\x01" * 16])
def test_forkchoice_reports_execution_only(custody: bytes | None) -> None:
    """Do not add an inclusion context parameter to forkchoice updates."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.response_validation_context = {}
    rpc.post_request = Mock()
    rpc.post_request.return_value.result_or_raise.return_value = {
        "payloadStatus": {
            "status": "VALID",
            "latestValidHash": str(Hash(1)),
            "validationError": None,
        },
        "payloadId": None,
    }
    result = rpc.forkchoice_updated(
        ForkchoiceState(head_block_hash=Hash(1)),
        version=5,
        custody_columns=custody,
    )
    assert result.payload_status.inclusion_list_satisfied is None
    params = rpc.post_request.call_args.kwargs["request"].params
    assert params[1:] == (
        [None] if custody is None else [None, f"0x{custody.hex()}"]
    )
