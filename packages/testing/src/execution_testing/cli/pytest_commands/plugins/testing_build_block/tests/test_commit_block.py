"""Unit tests for ``commit_block`` dispatch helpers."""

from typing import Any, List
from unittest.mock import MagicMock

import pytest

from execution_testing.base_types import Hash
from execution_testing.cli.pytest_commands.plugins.testing_build_block.commit_block import (  # noqa: E501
    commit_via_build,
    commit_via_commit,
)
from execution_testing.forks import get_forks
from execution_testing.rpc.rpc_types import (
    PayloadStatus,
    PayloadStatusEnum,
)


def _latest_fork() -> Any:
    """Return the latest known fork class."""
    return get_forks()[-1]


def _make_fake_payload(
    parent_hash: Hash, block_number: int, timestamp: int
) -> MagicMock:
    """Produce a minimal ``GetPayloadResponse`` stand-in."""
    exec_payload = MagicMock()
    exec_payload.block_hash = Hash(0xDEADBEEF)
    exec_payload.parent_hash = parent_hash
    exec_payload.number = block_number
    exec_payload.timestamp = timestamp
    payload = MagicMock()
    payload.execution_payload = exec_payload
    payload.blobs_bundle = None
    payload.execution_requests = None
    return payload


def test_build_mode_call_order() -> None:
    """``commit_via_build`` calls build, newPayload, then FCU."""
    calls: List[str] = []

    eth_rpc = MagicMock()
    eth_rpc.get_block_by_number.return_value = {
        "hash": "0x" + "11" * 32,
        "number": hex(100),
        "timestamp": hex(1_700_000_000),
    }

    testing_rpc = MagicMock()

    def _build(*_args: Any, **_kwargs: Any) -> MagicMock:
        calls.append("build_block")
        return _make_fake_payload(Hash("0x" + "11" * 32), 101, 1_700_000_001)

    testing_rpc.build_block.side_effect = _build

    engine_rpc = MagicMock()

    def _new_payload(*_args: Any, **_kwargs: Any) -> PayloadStatus:
        calls.append("new_payload")
        return PayloadStatus(
            status=PayloadStatusEnum.VALID,
            latest_valid_hash=Hash(0xDEADBEEF),
            validation_error=None,
        )

    engine_rpc.new_payload.side_effect = _new_payload

    def _fcu(*_args: Any, **_kwargs: Any) -> MagicMock:
        calls.append("forkchoice_updated")
        resp = MagicMock()
        resp.payload_status.status = PayloadStatusEnum.VALID
        return resp

    engine_rpc.forkchoice_updated.side_effect = _fcu

    new_head = commit_via_build(
        testing_rpc=testing_rpc,
        engine_rpc=engine_rpc,
        eth_rpc=eth_rpc,
        fork=_latest_fork(),
        txs=[],
        version=1,
    )

    assert calls == ["build_block", "new_payload", "forkchoice_updated"]
    assert new_head == Hash(0xDEADBEEF)
    # Build must be invoked with the parent head hash.
    build_kwargs = testing_rpc.build_block.call_args.kwargs
    assert build_kwargs["parent_block_hash"] == Hash("0x" + "11" * 32)
    assert build_kwargs["version"] == 1


def test_build_mode_asserts_on_invalid_new_payload() -> None:
    """Invalid ``newPayload`` status trips the build-mode assertion."""
    eth_rpc = MagicMock()
    eth_rpc.get_block_by_number.return_value = {
        "hash": "0x" + "22" * 32,
        "number": hex(5),
        "timestamp": hex(1_700_000_000),
    }
    testing_rpc = MagicMock()
    testing_rpc.build_block.return_value = _make_fake_payload(
        Hash("0x" + "22" * 32), 6, 1_700_000_001
    )
    engine_rpc = MagicMock()
    engine_rpc.new_payload.return_value = PayloadStatus(
        status=PayloadStatusEnum.INVALID,
        latest_valid_hash=None,
        validation_error=None,
    )

    with pytest.raises(AssertionError, match="engine_newPayload rejected"):
        commit_via_build(
            testing_rpc=testing_rpc,
            engine_rpc=engine_rpc,
            eth_rpc=eth_rpc,
            fork=_latest_fork(),
            txs=[],
        )


def test_commit_mode_posts_testing_commit_block() -> None:
    """``commit_via_commit`` posts ``testing_commitBlockVX``."""
    eth_rpc = MagicMock()
    eth_rpc.get_block_by_number.return_value = {
        "hash": "0x" + "33" * 32,
        "number": hex(42),
        "timestamp": hex(1_700_000_000),
    }

    new_head_hex = "0x" + "ab" * 32

    testing_rpc = MagicMock()
    response = MagicMock()
    response.result_or_raise.return_value = new_head_hex
    testing_rpc.post_request.return_value = response

    head = commit_via_commit(
        testing_rpc=testing_rpc,
        eth_rpc=eth_rpc,
        fork=_latest_fork(),
        txs=[],
        version=1,
    )

    assert head == Hash(new_head_hex)
    post_kwargs = testing_rpc.post_request.call_args.kwargs
    call = post_kwargs["request"]
    assert call.method == "commitBlockV1"
    # params: [payload_attributes, tx_rlp_list, extra_data]
    assert isinstance(call.params, list)
    assert len(call.params) == 3
    assert call.params[1] == []
    assert call.params[2] is None


def test_commit_mode_asserts_on_null_result() -> None:
    """A null RPC result raises so callers see the failure."""
    eth_rpc = MagicMock()
    eth_rpc.get_block_by_number.return_value = {
        "hash": "0x" + "44" * 32,
        "number": hex(7),
        "timestamp": hex(1_700_000_000),
    }
    testing_rpc = MagicMock()
    response = MagicMock()
    response.result_or_raise.return_value = None
    testing_rpc.post_request.return_value = response

    with pytest.raises(AssertionError, match="returned null"):
        commit_via_commit(
            testing_rpc=testing_rpc,
            eth_rpc=eth_rpc,
            fork=_latest_fork(),
            txs=[],
        )


if __name__ == "__main__":  # pragma: no cover - manual invocation
    pytest.main([__file__, "-v"])
