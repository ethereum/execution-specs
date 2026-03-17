"""Witness state collection scenarios for storage reads."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    ExecutionWitnessStateExpectation,
    Op,
    Transaction,
)

from .state_helpers import (
    as_storage,
    build_large_storage,
    collect_storage_path_only_nodes,
    collect_storage_proof_nodes,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_witness_state_sload_contains_storage_proof(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """SLOAD should include the pre-state proof for the loaded slot."""
    storage = build_large_storage([1])
    proof_nodes = collect_storage_proof_nodes(storage, [1])
    assert proof_nodes

    contract = pre.deploy_contract(
        code=Op.SLOAD(1) + Op.POP + Op.STOP,
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


def test_witness_state_reverted_sload_still_contains_storage_proof(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """A reverted SLOAD should still leave its proof nodes in witness state."""
    storage = build_large_storage([1])
    proof_nodes = collect_storage_proof_nodes(storage, [1])
    assert proof_nodes

    contract = pre.deploy_contract(
        code=Op.SLOAD(1) + Op.POP + Op.REVERT(0, 0),
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


def test_witness_state_sload_absent_slot_contains_storage_proof(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    SLOAD of an absent slot should include the pre-state absence proof.

    Use a multi-slot trie so the absent-slot path is meaningfully different
    from a single-leaf root.
    """
    storage = build_large_storage([1, 2])
    absent_slot = 3
    proof_nodes = collect_storage_proof_nodes(storage, [absent_slot])
    slot_1_only_nodes = collect_storage_path_only_nodes(
        storage, 1, [absent_slot]
    )
    slot_2_only_nodes = collect_storage_path_only_nodes(
        storage, 2, [absent_slot]
    )
    existing_slot_only_nodes = slot_1_only_nodes + slot_2_only_nodes
    assert proof_nodes
    assert len(slot_1_only_nodes) == 1
    assert len(slot_2_only_nodes) == 1

    contract = pre.deploy_contract(
        code=Op.SLOAD(absent_slot) + Op.POP + Op.STOP,
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
                        nodes_absent=existing_slot_only_nodes,
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage=storage),
        },
    )
