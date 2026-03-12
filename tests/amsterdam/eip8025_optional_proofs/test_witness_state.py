"""Witness state collection scenarios."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    ExecutionWitnessStateExpectation,
    Op,
    Storage,
    Transaction,
)

from .state_helpers import (
    build_large_storage,
    collect_storage_delete_auxiliary_nodes,
    collect_storage_post_state_only_nodes,
    collect_storage_path_only_nodes,
    collect_storage_proof_nodes,
    large_storage_value,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_witness_state_structural_invariants(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    A simple transfer is enough to validate the shared state invariants.

    The expectation object always checks for duplicate entries and sorted
    order even when no explicit state nodes are listed.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    tx = Transaction(sender=sender, to=recipient, value=1, gas_limit=21_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation()
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=1),
        },
    )


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
        storage=Storage(storage),
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
        storage=Storage(storage),
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


def test_witness_state_sstore_delete_branch_collapse_adds_auxiliary_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Deleting slot 1 from the `{1, 2}` trie shape forces branch collapse.

    The witness should contain both the normal proof for slot 1 and the
    auxiliary node needed to preserve the untouched sibling subtree.
    """
    storage = build_large_storage([1, 2])
    proof_nodes = collect_storage_proof_nodes(storage, [1])
    auxiliary_nodes = collect_storage_delete_auxiliary_nodes(storage, 1)
    assert proof_nodes
    # Double check the auxiliary node after the deletion resulted in
    # exactly one MPT node.
    assert len(auxiliary_nodes) == 1

    contract = pre.deploy_contract(
        code=Op.SSTORE(1, 0) + Op.STOP,
        storage=Storage(storage),
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
                        nodes_present=proof_nodes + auxiliary_nodes,
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage={2: storage[2]}),
        },
    )


def test_witness_state_sstore_delete_without_collapse_omits_sibling_nodes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Deleting slot 1 from the `{1, 2, 3}` trie shape does not collapse.

    The untouched sibling path should remain absent from the witness.
    """
    storage = build_large_storage([1, 2, 3])
    proof_nodes = collect_storage_proof_nodes(storage, [1])
    auxiliary_nodes = collect_storage_delete_auxiliary_nodes(storage, 1)
    sibling_only_nodes = collect_storage_path_only_nodes(storage, 2, [1])
    assert proof_nodes
    assert not auxiliary_nodes
    assert sibling_only_nodes

    contract = pre.deploy_contract(
        code=Op.SSTORE(1, 0) + Op.STOP,
        storage=Storage(storage),
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
                        nodes_absent=sibling_only_nodes,
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage={2: storage[2], 3: storage[3]}),
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
        storage=Storage(storage),
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


def test_witness_state_delete_with_new_dirty_sibling_omits_post_state_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    A sibling created before branch collapse is dirty and should not leak.

    The witness still needs the pre-state delete proof for slot 1 and the
    pre-state absence proof for slot 2, but it must not include the node
    created only after slot 2 is inserted during execution.
    """
    pre_storage = build_large_storage([1])
    post_storage = {2: large_storage_value(2)}
    proof_nodes = collect_storage_proof_nodes(pre_storage, [1, 2])
    post_state_only_nodes = collect_storage_post_state_only_nodes(
        pre_storage=pre_storage,
        post_storage=post_storage,
        slot=2,
        pre_state_reference_slots=[1, 2],
    )
    assert proof_nodes
    assert post_state_only_nodes

    contract = pre.deploy_contract(
        code=Op.SSTORE(2, post_storage[2]) + Op.SSTORE(1, 0) + Op.STOP,
        storage=Storage(pre_storage),
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


def test_witness_state_delete_with_modified_dirty_sibling_omits_post_state_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    A pre-state sibling that becomes dirty before collapse should not leak.

    The delete still requires the pre-state proof material, but the updated
    surviving child is dirty and must not be re-recorded as auxiliary.
    """
    pre_storage = build_large_storage([1, 2])
    post_storage = {2: large_storage_value(9)}
    proof_nodes = collect_storage_proof_nodes(pre_storage, [1, 2])
    post_state_only_nodes = collect_storage_post_state_only_nodes(
        pre_storage=pre_storage,
        post_storage=post_storage,
        slot=2,
        pre_state_reference_slots=[1, 2],
    )
    assert proof_nodes
    assert post_state_only_nodes

    contract = pre.deploy_contract(
        code=Op.SSTORE(2, post_storage[2]) + Op.SSTORE(1, 0) + Op.STOP,
        storage=Storage(pre_storage),
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
