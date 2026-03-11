"""Witness bytecode scenarios for system contracts."""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessCodesExpectation,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_witness_codes_empty_block_has_system_contracts(
    pre: Alloc,
    system_codes: list[Bytes],
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify an empty block contains only system contract bytecodes.

    System contracts are called every block via process_system_call,
    which calls get_code() on a tracked TransactionState. An empty
    block (no user transactions) should have exactly the four system
    contract bytecodes in executionWitness.codes and nothing else.
    """
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=system_codes,
                        allow_unexpected=False,
                    )
                ),
            )
        ],
        post={},
    )
