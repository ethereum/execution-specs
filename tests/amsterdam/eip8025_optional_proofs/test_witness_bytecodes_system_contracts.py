"""Witness bytecode scenarios for system contracts."""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    ExecutionWitnessCodesExpectation,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_witness_codes_empty_block_has_system_contracts(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify an empty block contains only system contract bytecodes.

    System contract codes are automatically added to codes_present
    by the testing framework, so an empty expectation is sufficient.
    The exhaustiveness check ensures no extra codes appear.
    """
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation()
                ),
            )
        ],
        post={},
    )
