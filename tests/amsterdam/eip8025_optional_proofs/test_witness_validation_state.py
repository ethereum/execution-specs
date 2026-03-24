"""Execution witness state validation tests."""

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
from execution_testing.test_types.execution_witness.modifiers import (
    remove_state_node,
)

from .state_helpers import (
    as_storage,
    build_large_storage,
    collect_storage_proof_nodes,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_validation_state_missing_storage_proof_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing a required storage proof node should fail the guest."""
    read_slot = 1
    write_slot = 2
    storage = build_large_storage([read_slot])
    proof_nodes = collect_storage_proof_nodes(storage, [read_slot])
    assert proof_nodes
    removed_node = sorted(proof_nodes)[0]

    contract = pre.deploy_contract(
        code=Op.SSTORE(write_slot, Op.SLOAD(read_slot)) + Op.STOP,
        storage=as_storage(storage),
    )
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract, gas_limit=500_000)
    post_storage = storage | {write_slot: storage[read_slot]}

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_present=proof_nodes,
                    ).modify(remove_state_node(removed_node))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage=post_storage),
        },
    )
