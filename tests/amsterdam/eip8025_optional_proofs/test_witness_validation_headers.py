"""Execution witness header validation tests."""

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
from execution_testing.test_types.execution_witness.modifiers import (
    clear_headers,
    remove_header_at,
    replace_header_at,
    reverse_headers,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_validation_headers_missing_parent_header(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the parent header from the witness should fail."""
    offset = 2
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


def test_validation_headers_missing_oldest_blockhash_ancestor(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the oldest required BLOCKHASH ancestor should fail."""
    offset = 5
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
                ).modify(remove_header_at(0))
            ),
            expected_stateless_validation_success=False,
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={sender: Account(nonce=1)},
    )


def test_validation_headers_non_contiguous_chain(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Reordering headers into a non-contiguous chain should fail."""
    offset = 5
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
                ).modify(reverse_headers())
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


def test_validation_headers_malformed_rlp_header(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Replacing a required header with malformed RLP should fail."""
    offset = 5
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
                ).modify(replace_header_at(-1, Bytes(b"\xff")))
            ),
            expected_stateless_validation_success=False,
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={sender: Account(nonce=1)},
    )
