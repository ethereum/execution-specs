"""Execution witness soundness tests."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessCodesExpectation,
    ExecutionWitnessHeadersExpectation,
    ExecutionWitnessStateExpectation,
    Op,
    Transaction,
)
from execution_testing.test_types.execution_witness.modifiers import (
    remove_code,
    remove_header_at,
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


def test_witness_soundness_missing_required_header(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the parent header from the witness should fail the guest."""
    offset = 2
    code = Op.BLOCKHASH(Op.SUB(Op.NUMBER, offset)) + Op.POP + Op.STOP
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

    blocks = [Block(txs=[]) for _ in range(offset)]
    blocks.append(
        Block(
            txs=[tx],
            expected_execution_witness_headers=(
                ExecutionWitnessHeadersExpectation(
                    expected_count=offset,
                ).modify(remove_header_at(-1))
            ),
            expected_stateless_validation_success=False,
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={sender: Account(nonce=1)},
    )


def test_witness_soundness_missing_caller_code(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the caller bytecode should fail guest re-execution."""
    target_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    target = pre.deploy_contract(code=target_code)

    caller_code = Op.EXTCODESIZE(target) + Op.POP + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)
    caller_code_bytes = Bytes(bytes(caller_code))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            caller_code_bytes,
                            Bytes(bytes(target_code)),
                        ],
                    ).modify(remove_code(caller_code_bytes))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


def test_witness_soundness_missing_storage_proof_node(
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
