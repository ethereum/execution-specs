"""Witness bytecode scenarios for system contracts."""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    ExecutionWitnessCodesExpectation,
)

from .spec import ref_spec_8025

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = ref_spec_8025.git_path
REFERENCE_SPEC_VERSION = ref_spec_8025.version


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
