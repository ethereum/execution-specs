"""Witness bytecode collection scenarios."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessCodesExpectation,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_witness_excludes_bytecode_created_in_same_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Create a contract in a block without reading its code first.

    The deployed runtime code should not appear in
    executionWitness.codes for this block.
    """
    runtime_code = bytes.fromhex("deadbeef")
    creator = pre.fund_eoa()
    created_contract = compute_create_address(address=creator, nonce=0)

    create_tx = Transaction(
        sender=creator,
        to=None,
        data=Initcode(deploy_code=runtime_code),
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[create_tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_absent=[Bytes(runtime_code)],
                    )
                ),
            )
        ],
        post={
            creator: Account(nonce=1),
            created_contract: Account(
                nonce=1,
                code=runtime_code,
            ),
        },
    )


def test_witness_keeps_prestate_code_read_even_if_later_created_with_same_hash(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Tx1 reads pre-state code, tx2 later deploys the same runtime code hash.

    The pre-state bytecode should appear in executionWitness.codes because
    tx1 CALLs an existing pre-state contract with that code.
    """
    runtime_code = bytes(Op.PUSH1(0x00) + Op.PUSH1(0x00) + Op.RETURN)

    existing_contract = pre.deploy_contract(code=runtime_code)

    reader = pre.fund_eoa()
    creator = pre.fund_eoa()
    created_contract = compute_create_address(address=creator, nonce=0)

    tx1_read_existing_code = Transaction(
        sender=reader,
        to=existing_contract,
        gas_limit=200_000,
    )
    tx2_create_same_code_hash = Transaction(
        sender=creator,
        to=None,
        data=Initcode(deploy_code=runtime_code),
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    tx1_read_existing_code,
                    tx2_create_same_code_hash,
                ],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(runtime_code)],
                    )
                ),
            )
        ],
        post={
            reader: Account(nonce=1),
            creator: Account(nonce=1),
            created_contract: Account(
                nonce=1,
                code=runtime_code,
            ),
        },
    )
