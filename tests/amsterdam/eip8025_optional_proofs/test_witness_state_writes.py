"""Witness state collection scenarios for storage writes."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessStateExpectation,
    Op,
    Transaction,
)

from .state_helpers import (
    as_storage,
    build_large_storage,
    collect_storage_post_state_only_nodes,
    collect_storage_proof_nodes,
    large_storage_value,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_witness_state_sstore_without_explicit_read_contains_storage_proof(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Dirty storage writes should still include the pre-state proof."""
    storage = build_large_storage([1])
    proof_nodes = collect_storage_proof_nodes(storage, [1])
    assert proof_nodes

    new_value = large_storage_value(9)
    contract = pre.deploy_contract(
        code=Op.SSTORE(1, new_value) + Op.STOP,
        storage=as_storage(storage),
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
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage={1: new_value}),
        },
    )


def test_witness_state_reverted_sstore_still_contains_storage_proof(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    A reverted SSTORE should still leave its proof nodes in witness.
    """
    storage = build_large_storage([1])
    proof_nodes = collect_storage_proof_nodes(storage, [1])
    assert proof_nodes

    new_value = large_storage_value(9)
    contract = pre.deploy_contract(
        code=Op.SSTORE(1, new_value) + Op.REVERT(0, 0),
        storage=as_storage(storage),
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
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage=storage),
        },
    )


def test_witness_state_sstore_new_slot_omits_post_state_nodes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Inserting a new slot should include the pre-state absence proof only.

    Nodes created solely by the post-state insertion must not leak into the
    witness.
    """
    pre_storage = build_large_storage([1, 2])
    insert_slot = 3
    insert_value = large_storage_value(insert_slot)
    post_storage = {
        **pre_storage,
        insert_slot: insert_value,
    }
    proof_nodes = collect_storage_proof_nodes(pre_storage, [insert_slot])
    post_state_only_nodes = collect_storage_post_state_only_nodes(
        pre_storage=pre_storage,
        post_storage=post_storage,
        slot=insert_slot,
        pre_state_reference_slots=[insert_slot],
    )
    assert proof_nodes
    assert post_state_only_nodes

    contract = pre.deploy_contract(
        code=Op.SSTORE(insert_slot, insert_value) + Op.STOP,
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
                        nodes_absent=post_state_only_nodes,
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage=post_storage),
        },
    )


def test_witness_state_sstore_into_empty_storage_omits_post_state_nodes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Empty pre-state storage should not require any storage proof nodes.

    The empty-trie RLP sentinel and nodes created solely by the insertion
    are not pre-state material and must not appear in the witness.
    """
    insert_slot = 1
    insert_value = large_storage_value(insert_slot)
    pre_storage: dict[int, int] = {}
    post_storage = {insert_slot: insert_value}
    proof_nodes = collect_storage_proof_nodes(pre_storage, [insert_slot])
    post_state_only_nodes = collect_storage_post_state_only_nodes(
        pre_storage=pre_storage,
        post_storage=post_storage,
        slot=insert_slot,
        pre_state_reference_slots=[insert_slot],
    )
    assert not proof_nodes
    assert post_state_only_nodes
    empty_trie_sentinel = Bytes(b"\x80")

    contract = pre.deploy_contract(
        code=Op.SSTORE(insert_slot, insert_value) + Op.STOP,
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
                        nodes_absent=post_state_only_nodes
                        + [empty_trie_sentinel],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage=post_storage),
        },
    )
