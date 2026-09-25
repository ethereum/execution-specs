"""Witness bytecode scenarios for precompiles and EOAs (negative cases)."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    ExecutionWitnessCodesExpectation,
    Transaction,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.with_all_precompiles()
def test_witness_codes_call_precompile(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    precompile: Address,
) -> None:
    """
    Send a transaction directly to a precompile.

    Precompile accounts have EMPTY_CODE_HASH, code tracking returns
    early without recording a code read.  The witness must contain
    only system contract bytecodes — nothing for the precompile.
    """
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=precompile, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation()
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


def test_witness_codes_call_eoa(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Send a value transfer directly to a plain EOA.

    EOAs with no delegations have EMPTY_CODE_HASH, so code tracking
    returns early without recording a code read.  The witness must
    contain only system contract bytecodes — nothing for the EOA.
    """
    eoa_target = pre.fund_eoa()

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=eoa_target,
        value=1,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation()
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )
