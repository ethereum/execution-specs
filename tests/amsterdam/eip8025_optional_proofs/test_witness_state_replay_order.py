"""Witness state collection scenarios for storage replay ordering."""

import pytest
from ethereum_types.bytes import Bytes32
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Conditional,
    ExecutionWitnessStateExpectation,
    Op,
    Transaction,
)

from ethereum.crypto.hash import keccak256

from .state_helpers import (
    as_storage,
    build_large_storage,
    collect_storage_delete_auxiliary_nodes,
    collect_storage_proof_nodes,
    large_storage_value,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def _secured_storage_key(slot: int) -> bytes:
    """Return the secured trie key used for a storage slot."""
    return keccak256(Bytes32(slot.to_bytes(32, byteorder="big")))


def test_witness_state_delete_then_insert_uses_insert_before_delete_order(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    EL post-state root calculation must insert before deleting.

    Deleting slot 1 from `{1, 2}` would normally require the clean sibling
    auxiliary node for slot 2. Computing the correct post-state root avoids
    that collapse by replaying the slot 3 insertion before the slot 1
    deletion. The chosen slots also catch buggy key-sorted replay: slot 1's
    secured trie key sorts before slot 3's, so sorting still deletes too
    early.
    """
    delete_slot = 1
    preserved_slot = 2
    insert_slot = 3
    insert_value = large_storage_value(insert_slot)
    pre_storage = build_large_storage([delete_slot, preserved_slot])
    post_storage = {
        preserved_slot: pre_storage[preserved_slot],
        insert_slot: insert_value,
    }
    proof_nodes = collect_storage_proof_nodes(
        pre_storage, [delete_slot, insert_slot]
    )
    auxiliary_nodes = collect_storage_delete_auxiliary_nodes(
        pre_storage, delete_slot
    )
    assert proof_nodes
    assert len(auxiliary_nodes) == 1
    assert not set(proof_nodes) & set(auxiliary_nodes)
    # This slot choice also catches clients that sort secured trie keys:
    # slot 1 sorts before slot 3, so a buggy key-sorted replay still
    # deletes before it inserts.
    assert _secured_storage_key(delete_slot) < _secured_storage_key(
        insert_slot
    )

    contract = pre.deploy_contract(
        code=Op.SSTORE(delete_slot, 0)
        + Op.SSTORE(insert_slot, insert_value)
        + Op.STOP,
        storage=as_storage(pre_storage),
    )
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_present=proof_nodes,
                        nodes_absent=auxiliary_nodes,
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage=post_storage),
        },
    )


def test_witness_state_block_diff_delete_insert_before_delete_order(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Reproduces the same post-state-root ordering case as the
    single-transaction test, but across transactions.

    The block-level diff records slot 1 before slot 3 because the delete
    transaction executes first. Even so, EL post-state root calculation
    must still insert slot 3 before deleting slot 1. The chosen slots also
    catch buggy key-sorted replay because slot 1's secured trie key sorts
    before slot 3's.
    """
    delete_slot = 1
    preserved_slot = 2
    insert_slot = 3
    insert_value = large_storage_value(insert_slot)
    pre_storage = build_large_storage([delete_slot, preserved_slot])
    post_storage = {
        preserved_slot: pre_storage[preserved_slot],
        insert_slot: insert_value,
    }
    proof_nodes = collect_storage_proof_nodes(
        pre_storage, [delete_slot, insert_slot]
    )
    auxiliary_nodes = collect_storage_delete_auxiliary_nodes(
        pre_storage, delete_slot
    )
    assert proof_nodes
    assert len(auxiliary_nodes) == 1
    assert not set(proof_nodes) & set(auxiliary_nodes)
    # This slot choice also catches clients that sort secured trie keys:
    # slot 1 sorts before slot 3, so a buggy key-sorted replay still
    # deletes before it inserts.
    assert _secured_storage_key(delete_slot) < _secured_storage_key(
        insert_slot
    )

    contract = pre.deploy_contract(
        code=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 0),
            if_true=Op.SSTORE(delete_slot, 0),
            if_false=Op.SSTORE(insert_slot, insert_value),
        )
        + Op.STOP,
        storage=as_storage(pre_storage),
    )
    sender = pre.fund_eoa()
    tx_delete = Transaction(
        sender=sender,
        to=contract,
        gas_limit=500_000,
        nonce=0,
    )
    tx_insert = Transaction(
        sender=sender,
        to=contract,
        gas_limit=500_000,
        data=(1).to_bytes(32, byteorder="big"),
        nonce=1,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx_delete, tx_insert],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_present=proof_nodes,
                        nodes_absent=auxiliary_nodes,
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=2),
            contract: Account(storage=post_storage),
        },
    )
