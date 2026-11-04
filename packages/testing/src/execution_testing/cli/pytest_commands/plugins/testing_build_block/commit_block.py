"""Dispatch block-commit flows across ``testing_*`` RPC variants."""

from typing import Any, List, Sequence

from execution_testing.base_types import (
    Address,
    Bytes,
    Hash,
    HexNumber,
    to_json,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.rpc import EngineRPC, EthRPC, RPCCall, TestingRPC
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    PayloadAttributes,
    PayloadStatusEnum,
    TransactionProtocol,
)


def _payload_attributes_for_fork(
    fork: Fork | TransitionFork,
    next_block_number: int,
    next_timestamp: int,
) -> PayloadAttributes:
    """
    Assemble ``PayloadAttributes`` for the block to build.

    Mirrors ``ChainBuilderEthRPC._payload_attributes`` so behaviour stays
    consistent with the main EEST chain-builder path.
    """
    next_fork = fork.fork_at(
        block_number=next_block_number, timestamp=next_timestamp
    )
    parent_beacon_block_root = (
        Hash(0) if next_fork.header_beacon_root_required() else None
    )
    target_blobs = (
        next_fork.target_blobs_per_block()
        if next_fork.engine_payload_attribute_target_blobs_per_block()
        else None
    )
    max_blobs = (
        next_fork.max_blobs_per_block()
        if next_fork.engine_payload_attribute_max_blobs_per_block()
        else None
    )
    return PayloadAttributes(
        timestamp=HexNumber(next_timestamp),
        prev_randao=Hash(0),
        suggested_fee_recipient=Address(0),
        withdrawals=([] if next_fork.header_withdrawals_required() else None),
        parent_beacon_block_root=parent_beacon_block_root,
        target_blobs_per_block=(
            HexNumber(target_blobs) if target_blobs is not None else None
        ),
        max_blobs_per_block=(
            HexNumber(max_blobs) if max_blobs is not None else None
        ),
    )


def commit_via_build(
    testing_rpc: TestingRPC,
    engine_rpc: EngineRPC,
    eth_rpc: EthRPC,
    fork: Fork | TransitionFork,
    txs: Sequence[TransactionProtocol],
    *,
    version: int = 1,
) -> Hash:
    """
    Build a block and advance head via Engine API.

    Executes ``testing_buildBlockVX`` on top of the current ``latest``
    head, then submits the resulting payload through
    ``engine_newPayloadVn`` and ``engine_forkchoiceUpdatedVn``. Returns
    the hash of the new canonical head.
    """
    head = eth_rpc.get_block_by_number("latest")
    assert head is not None, "Cannot resolve latest head block"
    parent_hash = Hash(head["hash"])
    parent_number = int(HexNumber(head["number"]))
    parent_timestamp = int(HexNumber(head["timestamp"]))
    next_block_number = parent_number + 1
    next_timestamp = parent_timestamp + 1

    payload_attributes = _payload_attributes_for_fork(
        fork, next_block_number, next_timestamp
    )
    payload = testing_rpc.build_block(
        parent_block_hash=parent_hash,
        payload_attributes=payload_attributes,
        transactions=txs,
        extra_data=Bytes(b""),
        version=version,
    )

    payload_fork = fork.fork_at(
        block_number=payload.execution_payload.number,
        timestamp=payload.execution_payload.timestamp,
    )
    new_payload_args: List[Any] = [payload.execution_payload]
    if payload.blobs_bundle is not None:
        new_payload_args.append(payload.blobs_bundle.blob_versioned_hashes())
    if payload_attributes.parent_beacon_block_root is not None:
        new_payload_args.append(payload_attributes.parent_beacon_block_root)
    if payload.execution_requests is not None:
        new_payload_args.append(payload.execution_requests)

    new_payload_version = payload_fork.engine_new_payload_version()
    assert new_payload_version is not None, (
        "Fork does not support engine new_payload"
    )
    new_payload_response = engine_rpc.new_payload(
        *new_payload_args, version=new_payload_version
    )
    assert new_payload_response.status == PayloadStatusEnum.VALID, (
        f"engine_newPayload rejected built block: "
        f"{new_payload_response.status}"
    )

    fcu_version = payload_fork.engine_forkchoice_updated_version()
    assert fcu_version is not None, (
        "Fork does not support engine forkchoice_updated"
    )
    new_head_hash = Hash(payload.execution_payload.block_hash)
    fcu_response = engine_rpc.forkchoice_updated(
        ForkchoiceState(head_block_hash=new_head_hash),
        None,
        version=fcu_version,
    )
    assert fcu_response.payload_status.status == PayloadStatusEnum.VALID, (
        f"engine_forkchoiceUpdated rejected new head: "
        f"{fcu_response.payload_status.status}"
    )
    return new_head_hash


def commit_via_commit(
    testing_rpc: TestingRPC,
    eth_rpc: EthRPC,
    fork: Fork | TransitionFork,
    txs: Sequence[TransactionProtocol],
    *,
    version: int = 1,
) -> Hash:
    """
    Single-shot ``testing_commitBlockV1`` dispatch.

    Reads the chain head from *eth_rpc* to derive fork-appropriate
    payload attributes, then delegates block creation and head
    advancement to the ``testing_commitBlockVX`` endpoint. No Engine
    API round-trip is needed: the client advances head itself and
    returns the committed block hash.
    """
    head = eth_rpc.get_block_by_number("latest")
    assert head is not None, "Cannot resolve latest head block"
    parent_number = int(HexNumber(head["number"]))
    parent_timestamp = int(HexNumber(head["timestamp"]))
    next_block_number = parent_number + 1
    next_timestamp = parent_timestamp + 1

    payload_attributes = _payload_attributes_for_fork(
        fork, next_block_number, next_timestamp
    )

    method = f"commitBlockV{version}"
    params: List[Any] = [
        to_json(payload_attributes),
        [tx.rlp().hex() for tx in txs],
        None,
    ]
    result = testing_rpc.post_request(
        request=RPCCall(method=method, params=params)
    ).result_or_raise()
    assert result is not None, (
        "testing_commitBlockV1 returned null; commit failed"
    )
    return Hash(result)
