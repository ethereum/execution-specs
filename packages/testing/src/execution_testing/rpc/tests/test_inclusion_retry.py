"""Exercise deferred inclusion verdicts bound to explicit request inputs."""

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
    verdict: bool | None = None, *, syncing: bool = False, check_id: int = 10
) -> PayloadStatus:
    """Return execution and inclusion statuses for one execution block."""
    return PayloadStatus(
        status=PayloadStatusEnum.SYNCING
        if syncing
        else PayloadStatusEnum.VALID,
        latest_valid_hash=None if syncing else Hash(1),
        validation_error=None,
        inclusion_list_satisfied=verdict,
        inclusion_check_id=None if syncing else Hash(check_id),
    )


@pytest.mark.parametrize("verdict", [True, False])
@pytest.mark.parametrize("syncing", [True, False])
def test_pending_verdict_polls_identifier(
    verdict: bool, syncing: bool
) -> None:
    """Resend inputs only for execution; poll inclusion with its identifier."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.new_payload = Mock(return_value=status())
    rpc.get_inclusion_list_verdict = Mock(side_effect=[None, verdict])
    claim = {"transactionHash": Hash(4), "evaluationIndex": "0x2"}
    inputs: tuple[Any, ...] = (
        {"blockHash": Hash(1)},
        [],
        Hash(0),
        [],
        [["0xc0", "0xc0"]] + [[]] * 15,
        [claim, claim],
    )
    result = rpc.wait_for_inclusion_list(
        status(syncing=syncing), *inputs, version=6, wait_fixed=0
    )
    assert result.inclusion_list_satisfied is verdict
    assert rpc.new_payload.call_count == int(syncing)
    assert rpc.get_inclusion_list_verdict.call_count == 2
    rpc.get_inclusion_list_verdict.assert_called_with(Hash(10))
    for call in rpc.new_payload.call_args_list:
        assert call.args == inputs
        assert call.kwargs == {"version": 6}


def test_same_execution_block_different_checks_have_separate_verdicts() -> (
    None
):
    """Do not confuse check identifiers for the same execution block."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.new_payload = Mock()
    rpc.get_inclusion_list_verdict = Mock(side_effect=[True, False])
    for check_id, verdict in [(10, True), (11, False)]:
        result = rpc.wait_for_inclusion_list(
            status(check_id=check_id), version=6, wait_fixed=0
        )
        assert result.inclusion_list_satisfied is verdict
        rpc.get_inclusion_list_verdict.assert_called_with(Hash(check_id))
    rpc.new_payload.assert_not_called()


def test_unknown_check_recovers_original_inputs() -> None:
    """Recover an evicted check without changing duplicate ILs or claims."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.get_inclusion_list_verdict = Mock(
        side_effect=[JSONRPCError(-38007, "Unknown inclusion check"), True]
    )
    rpc.new_payload = Mock(return_value=status())
    claim = {"transactionHash": Hash(4), "evaluationIndex": "0x2"}
    inputs: tuple[Any, ...] = (
        {"blockHash": Hash(1)},
        [],
        Hash(0),
        [],
        [["0xc0", "0xc0"]] + [[]] * 15,
        [claim, claim],
    )
    result = rpc.wait_for_inclusion_list(
        status(), *inputs, version=6, wait_fixed=0
    )
    assert result.inclusion_list_satisfied is True
    rpc.new_payload.assert_called_once_with(*inputs, version=6)


def test_pending_verdict_times_out() -> None:
    """A perpetually pending VALID payload must not pass the check."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.get_inclusion_list_verdict = Mock(return_value=None)
    with pytest.raises(TimeoutError, match="remained pending"):
        rpc.wait_for_inclusion_list(
            status(), version=6, max_attempts=2, wait_fixed=0
        )
    assert rpc.get_inclusion_list_verdict.call_count == 2


def test_retry_does_not_swallow_rpc_errors() -> None:
    """Propagate an RPC error instead of mistaking it for a pending verdict."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.get_inclusion_list_verdict = Mock(
        side_effect=JSONRPCError(-32603, "Internal error")
    )
    with pytest.raises(JSONRPCError, match="Internal error"):
        rpc.wait_for_inclusion_list(status(), version=6, wait_fixed=0)


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


@pytest.mark.parametrize("verdict", [None, True, False])
def test_verdict_query_wire_request(verdict: bool | None) -> None:
    """Send only the check identifier and preserve a pending null response."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.post_request = Mock()
    rpc.post_request.return_value.result_or_raise.return_value = verdict
    assert rpc.get_inclusion_list_verdict(Hash(10)) is verdict
    request = rpc.post_request.call_args.kwargs["request"]
    assert request.method == "getInclusionListVerdictV1"
    assert request.params == [str(Hash(10))]


def test_valid_response_requires_check_identifier() -> None:
    """Do not silently fall back to payload polling on a malformed response."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    response = status().model_copy(update={"inclusion_check_id": None})
    with pytest.raises(ValueError, match="lacks inclusion check ID"):
        rpc.wait_for_inclusion_list(response, version=6)
