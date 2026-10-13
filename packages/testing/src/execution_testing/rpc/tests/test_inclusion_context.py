"""Exercise deferred inclusion verdicts and context recovery."""

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
    context: int, verdict: bool | None = None, *, syncing: bool = False
) -> PayloadStatus:
    """Return distinct contexts for the same execution block."""
    return PayloadStatus(
        status=PayloadStatusEnum.SYNCING
        if syncing
        else PayloadStatusEnum.VALID,
        latest_valid_hash=None if syncing else Hash(1),
        validation_error=None,
        inclusion_list_satisfied=verdict,
        inclusion_list_context_id=Hash(context),
    )


@pytest.mark.parametrize("verdict", [True, False])
@pytest.mark.parametrize("syncing", [True, False])
def test_pending_context_resolves_without_resubmission(
    verdict: bool, syncing: bool
) -> None:
    """Execution VALID does not turn a pending check into satisfaction."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.get_inclusion_list_status = Mock(
        side_effect=[status(2), status(2, verdict)]
    )
    rpc.new_payload = Mock()
    result = rpc.wait_for_inclusion_list(
        status(2, syncing=syncing), version=6, wait_fixed=0
    )
    assert result.inclusion_list_satisfied is verdict
    assert rpc.get_inclusion_list_status.call_count == 2
    rpc.get_inclusion_list_status.assert_called_with(Hash(2))
    rpc.new_payload.assert_not_called()


def test_evicted_context_resubmits_original_inputs() -> None:
    """An expired handle preserves membership and ordered duplicate claims."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.get_inclusion_list_status = Mock(
        side_effect=[
            JSONRPCError(-38007, "Unknown inclusion context"),
            status(3, False),
        ]
    )
    rpc.new_payload = Mock(return_value=status(3))
    claim = {"transactionHash": Hash(4), "transactionIndex": "0x2"}
    inputs: tuple[Any, ...] = (
        {"blockHash": Hash(1)},
        [],
        Hash(0),
        [],
        ["0xc0"],
        ["0x0002"],
        [claim, claim],
    )
    result = rpc.wait_for_inclusion_list(
        status(2), *inputs, version=6, wait_fixed=0
    )
    assert result.inclusion_list_satisfied is False
    rpc.new_payload.assert_called_once_with(*inputs, version=6)
    assert [
        c.args[0] for c in rpc.get_inclusion_list_status.call_args_list
    ] == [Hash(2), Hash(3)]


def test_pending_context_times_out() -> None:
    """A perpetually pending VALID payload must not pass the check."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.get_inclusion_list_status = Mock(return_value=status(2))
    with pytest.raises(TimeoutError, match="remained pending"):
        rpc.wait_for_inclusion_list(
            status(2), version=6, max_attempts=2, wait_fixed=0
        )
    assert rpc.get_inclusion_list_status.call_count == 2


def test_query_rejects_another_context_for_same_block() -> None:
    """A verdict for the same execution hash can still be the wrong verdict."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.response_validation_context = {}
    rpc.post_request = Mock()
    rpc.post_request.return_value.result_or_raise.return_value = status(
        3, True
    ).model_dump(by_alias=True)
    with pytest.raises(ValueError, match="different context"):
        rpc.get_inclusion_list_status(Hash(2))


def test_query_does_not_swallow_other_rpc_errors() -> None:
    """Only unknown-context errors authorize resubmission."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.get_inclusion_list_status = Mock(
        side_effect=JSONRPCError(-32603, "Internal error")
    )
    rpc.new_payload = Mock()
    with pytest.raises(JSONRPCError, match="Internal error"):
        rpc.wait_for_inclusion_list(status(2), version=6, wait_fixed=0)
    rpc.new_payload.assert_not_called()


@pytest.mark.parametrize("custody", [None, b"\x01" * 16])
@pytest.mark.parametrize("mismatched", [False, True])
def test_forkchoice_context_is_fourth_parameter(
    custody: bytes | None, mismatched: bool
) -> None:
    """The head context cannot occupy the custody or child-attributes slot."""
    rpc: Any = EngineRPC.__new__(EngineRPC)
    rpc.response_validation_context = {}
    rpc.post_request = Mock()
    rpc.post_request.return_value.result_or_raise.return_value = {
        "payloadStatus": status(3 if mismatched else 2, False).model_dump(
            by_alias=True
        ),
        "payloadId": None,
    }
    if mismatched:
        with pytest.raises(ValueError, match="different context"):
            rpc.forkchoice_updated(
                ForkchoiceState(head_block_hash=Hash(1)),
                version=5,
                custody_columns=custody,
                inclusion_list_context_id=Hash(2),
            )
    else:
        result = rpc.forkchoice_updated(
            ForkchoiceState(head_block_hash=Hash(1)),
            version=5,
            custody_columns=custody,
            inclusion_list_context_id=Hash(2),
        )
        assert result.payload_status.inclusion_list_satisfied is False
    params = rpc.post_request.call_args.kwargs["request"].params
    assert params[1:] == [
        None,
        None if custody is None else f"0x{custody.hex()}",
        str(Hash(2)),
    ]
