"""Witness state collection scenarios for storage and account replay order."""

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
    compute_create_address,
)

from ethereum.crypto.hash import keccak256

from .spec import ref_spec_8025
from .state_helpers import (
    as_storage,
    build_large_storage,
    collect_account_delete_auxiliary_nodes,
    collect_account_path_only_nodes,
    collect_account_proof_nodes,
    collect_storage_delete_auxiliary_nodes,
    collect_storage_proof_nodes,
    find_accounts_sharing_branch,
    large_storage_value,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = ref_spec_8025.git_path
REFERENCE_SPEC_VERSION = ref_spec_8025.version


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


@pytest.mark.parametrize(
    "insert",
    [
        pytest.param(False, id="delete_only"),
        pytest.param(True, id="delete_then_insert"),
    ],
)
def test_witness_state_account_delete_uses_insert_before_delete_order(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    insert: bool,
) -> None:
    """
    EL post-state root calculation must insert accounts before deleting.

    Deleting an account collapses its branch onto the only sibling, whose
    leaf the witness then holds as an auxiliary node. Creating a third
    account under that branch in the same block avoids the collapse only if
    the insertion is replayed first. The deletion comes first in block
    order, address order and secured key order, so a replay in any of them
    deletes too early.
    """
    beneficiary_balance = 1
    deleted_balance = 2
    beneficiary = pre.fund_eoa(amount=beneficiary_balance)
    creator = pre.fund_eoa()
    # A funded address with no code and nonce 0 exists in the pre-state and
    # can still be deployed to. A contract that self-destructs in the
    # transaction that creates it is deleted.
    deleted = compute_create_address(address=creator, nonce=0)
    sibling, inserted = find_accounts_sharing_branch(pre, deleted)
    pre.fund_address(sibling, 1)
    pre.fund_address(deleted, deleted_balance)

    # Deleting on its own needs one node beyond the proof: the sibling's leaf.
    auxiliary_nodes = collect_account_delete_auxiliary_nodes(pre, deleted)
    assert len(auxiliary_nodes) == 1
    assert auxiliary_nodes == collect_account_path_only_nodes(
        pre, sibling, [deleted]
    )
    assert deleted < inserted
    assert keccak256(deleted) < keccak256(inserted)

    txs = [
        Transaction(sender=creator, to=None, data=Op.SELFDESTRUCT(beneficiary))
    ]
    post = {
        deleted: Account.NONEXISTENT,
        beneficiary: Account(balance=beneficiary_balance + deleted_balance),
        sibling: Account(balance=1),
    }
    if insert:
        txs.append(Transaction(sender=creator, to=inserted, value=1))
        post[inserted] = Account(balance=1)
        proof_nodes = collect_account_proof_nodes(pre, [deleted, inserted])
        assert not set(proof_nodes) & set(auxiliary_nodes)
        expectation = ExecutionWitnessStateExpectation(
            nodes_present=proof_nodes,
            nodes_absent=auxiliary_nodes,
        )
    else:
        expectation = ExecutionWitnessStateExpectation(
            nodes_present=collect_account_proof_nodes(pre, [deleted])
            + auxiliary_nodes,
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                expected_execution_witness_state=expectation,
                expected_stateless_validation_success=True,
            )
        ],
        post=post,
    )
