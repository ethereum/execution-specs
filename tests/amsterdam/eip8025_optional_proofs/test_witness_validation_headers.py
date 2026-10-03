"""Execution witness header validation tests."""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessHeadersExpectation,
    Op,
    Transaction,
)
from execution_testing.test_types.execution_witness import ExecutionWitness
from execution_testing.test_types.execution_witness.modifiers import (
    clear_headers,
    remove_header_at,
    replace_header_at,
    reverse_headers,
)

from .spec import ref_spec_8025

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = ref_spec_8025.git_path
REFERENCE_SPEC_VERSION = ref_spec_8025.version


@pytest.mark.parametrize(
    "offset,modifier",
    [
        pytest.param(2, remove_header_at(-1), id="missing_parent_header"),
        pytest.param(
            5,
            remove_header_at(0),
            id="missing_oldest_blockhash_ancestor",
        ),
        pytest.param(5, reverse_headers(), id="non_contiguous_chain"),
        pytest.param(
            5,
            replace_header_at(-1, Bytes(b"\xff")),
            id="malformed_rlp_header",
        ),
    ],
)
def test_validation_headers_invalid_ancestor_chain(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    offset: int,
    modifier: Callable[[ExecutionWitness], ExecutionWitness],
) -> None:
    """
    Removing, reordering or corrupting a required header should fail.
    """
    contract = pre.deploy_contract(
        code=Op.BLOCKHASH(Op.SUB(Op.NUMBER, offset)) + Op.POP + Op.STOP
    )
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

    blocks = [Block(txs=[]) for _ in range(offset)]
    blocks.append(
        Block(
            txs=[tx],
            expected_execution_witness_headers=(
                ExecutionWitnessHeadersExpectation(
                    expected_count=offset,
                ).modify(modifier)
            ),
            expected_stateless_validation_success=False,
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={sender: Account(nonce=1)},
    )


def test_validation_headers_empty_block_missing_mandatory_parent(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the mandatory parent header from an empty block should fail."""
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                expected_execution_witness_headers=(
                    ExecutionWitnessHeadersExpectation(
                        expected_count=1,
                    ).modify(clear_headers())
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={},
    )
