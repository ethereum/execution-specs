"""Witness state collection scenarios for state reads."""

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
    collect_account_proof_nodes,
    collect_storage_path_only_nodes,
    collect_storage_proof_nodes,
    merge_with_amsterdam_pre_alloc,
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


def test_witness_state_reverted_inner_sload_still_contains_storage_proof(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    A reverted inner-call SLOAD should still leave its proof nodes in witness.
    """
    storage = build_large_storage([1])
    proof_nodes = collect_storage_proof_nodes(storage, [1])
    assert proof_nodes

    callee = pre.deploy_contract(
        code=Op.SLOAD(1) + Op.POP + Op.REVERT(0, 0),
        storage=as_storage(storage),
    )
    caller = pre.deploy_contract(
        code=Op.CALL(Op.GAS, callee, 0, 0, 0, 0, 0) + Op.POP + Op.STOP,
    )
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

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
            callee: Account(storage=storage),
        },
    )


def test_witness_state_failed_call_still_contains_target_account_proof(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """A failed CALL should still include the target account proof."""
    target = pre.fund_eoa()
    caller_balance = 100
    transfer_value = 1_000
    caller_code = (
        Op.SSTORE(
            0,
            Op.CALL(
                Op.GAS,
                target,
                transfer_value,
                0,
                0,
                0,
                0,
            ),
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(
        code=caller_code,
        balance=caller_balance,
        storage={0: 1},
    )
    sender = pre.fund_eoa()
    full_alloc = merge_with_amsterdam_pre_alloc(pre)
    proof_nodes = collect_account_proof_nodes(full_alloc, [target])
    assert proof_nodes

    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

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
            caller: Account(balance=caller_balance, storage={0: 0}),
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
