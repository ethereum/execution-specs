"""Witness header collection border-case tests."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    ExecutionWitnessHeadersExpectation,
    Op,
    Transaction,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_witness_headers_empty_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test witness headers for an empty block (no user transactions).

    The only ancestor tracking comes from the EIP-2935 system contract
    which unconditionally records offset = 1 (parent header).
    """
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                expected_execution_witness_headers=(
                    ExecutionWitnessHeadersExpectation(
                        expected_count=1,
                    )
                ),
            ),
        ],
        post={},
    )


@pytest.mark.parametrize("offset", [1, 2, 5, 10])
def test_witness_headers_blockhash_at_offset(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    offset: int,
) -> None:
    """
    Test witness headers when BLOCKHASH queries a block at a given offset.

    offset = 1 matches the EIP-2935 baseline.
    offset > 1 verifies BLOCKHASH extends oldest_ancestor_offset beyond
    the system-contract baseline.
    """
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
                )
            ),
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={sender: Account(nonce=1)},
    )


@pytest.mark.parametrize(
    "queried_block_code",
    [
        pytest.param(Op.NUMBER, id="current_block"),
        pytest.param(Op.ADD(Op.NUMBER, 1), id="future_block"),
    ],
)
def test_witness_headers_blockhash_out_of_range(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    queried_block_code: Op,
) -> None:
    """
    Test witness headers when BLOCKHASH queries an out-of-range block.

    BLOCKHASH returns 0 for the current or future block numbers, so
    track_ancestor_access is never called by the opcode.  Only the
    EIP-2935 system-contract offset = 1 remains.
    """
    code = Op.BLOCKHASH(queried_block_code) + Op.POP + Op.STOP
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_headers=(
                    ExecutionWitnessHeadersExpectation(
                        expected_count=1,
                    )
                ),
            ),
        ],
        post={sender: Account(nonce=1)},
    )


def test_witness_headers_blockhash_in_reverted_tx(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test witness headers survive a full transaction revert.
    """
    offset = 5
    code = Op.BLOCKHASH(Op.SUB(Op.NUMBER, offset)) + Op.POP + Op.REVERT(0, 0)
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
                )
            ),
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={sender: Account(nonce=1)},
    )


@pytest.mark.parametrize(
    "offsets",
    [
        pytest.param([2, 8], id="ascending"),
        pytest.param([8, 2], id="descending"),
        pytest.param([3, 3], id="same_twice"),
    ],
)
def test_witness_headers_multiple_blockhash_max_wins(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    offsets: list[int],
) -> None:
    """
    Test that the maximum BLOCKHASH offset wins.

    Multiple BLOCKHASH calls in one contract: the ascending and
    descending cases prove order-independence.  The same_twice case
    confirms idempotent tracking.
    """
    code = Op.BLOCKHASH(Op.SUB(Op.NUMBER, offsets[0])) + Op.POP
    for o in offsets[1:]:
        code += Op.BLOCKHASH(Op.SUB(Op.NUMBER, o)) + Op.POP
    code += Op.STOP
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

    expected_count = max(offsets)
    blocks = [Block(txs=[]) for _ in range(expected_count)]
    blocks.append(
        Block(
            txs=[tx],
            expected_execution_witness_headers=(
                ExecutionWitnessHeadersExpectation(
                    expected_count=expected_count,
                )
            ),
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={sender: Account(nonce=1)},
    )


@pytest.mark.slow
@pytest.mark.parametrize(
    "offset,expected_count",
    [
        pytest.param(256, 256, id="max_valid"),
        pytest.param(257, 1, id="first_invalid"),
    ],
)
def test_witness_headers_blockhash_boundary(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    offset: int,
    expected_count: int,
) -> None:
    """
    Test witness headers at the exact boundary of the 256-block window.

    At offset = 256 the BLOCKHASH range check passes and all 256
    headers appear.  At offset = 257 the check fails, BLOCKHASH
    returns 0, no tracking occurs, and only the EIP-2935 parent
    header remains.
    """
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
                    expected_count=expected_count,
                )
            ),
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={sender: Account(nonce=1)},
    )
