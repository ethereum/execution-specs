"""Witness header collection border-case tests."""

from copy import deepcopy

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTest,
    BlockchainTestFiller,
    ExecutionWitnessHeadersExpectation,
    Op,
    Transaction,
)
from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures import BlockchainFixture
from execution_testing.fixtures.blockchain import FixtureBlock
from execution_testing.forks import Amsterdam
from execution_testing.test_types.execution_witness.modifiers import (
    prepend_header,
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


def test_witness_headers_max_wins_across_multiple_transactions(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    The deepest BLOCKHASH across all transactions drives the witness.
    """
    offset_small = 2
    offset_large = 5

    contract_small = pre.deploy_contract(
        code=Op.BLOCKHASH(Op.SUB(Op.NUMBER, offset_small)) + Op.POP + Op.STOP
    )
    contract_large = pre.deploy_contract(
        code=Op.BLOCKHASH(Op.SUB(Op.NUMBER, offset_large)) + Op.POP + Op.STOP
    )

    sender_small = pre.fund_eoa()
    sender_large = pre.fund_eoa()
    tx_small = Transaction(
        sender=sender_small,
        to=contract_small,
        gas_limit=500_000,
    )
    tx_large = Transaction(
        sender=sender_large,
        to=contract_large,
        gas_limit=500_000,
    )

    blocks = [Block(txs=[]) for _ in range(offset_large)]
    blocks.append(
        Block(
            txs=[tx_small, tx_large],
            expected_execution_witness_headers=(
                ExecutionWitnessHeadersExpectation(
                    expected_count=offset_large,
                )
            ),
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            sender_small: Account(nonce=1),
            sender_large: Account(nonce=1),
        },
    )


def test_witness_headers_blockhash_in_reverted_inner_call(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Header access in a reverted inner call should still be witnessed.
    """
    offset = 5
    callee = pre.deploy_contract(
        code=Op.BLOCKHASH(Op.SUB(Op.NUMBER, offset)) + Op.POP + Op.REVERT(0, 0)
    )
    caller = pre.deploy_contract(
        code=Op.CALL(Op.GAS, callee, 0, 0, 0, 0, 0) + Op.POP + Op.STOP
    )

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

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


def test_witness_headers_extra_unused_older_ancestor(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    t8n: TransitionTool,
) -> None:
    """
    A contiguous extra older ancestor should still validate.
    """
    offset = 3
    contract = pre.deploy_contract(
        code=Op.BLOCKHASH(Op.SUB(Op.NUMBER, offset)) + Op.POP + Op.STOP
    )
    sender = pre.fund_eoa()
    post = {sender: Account(nonce=1)}

    probe_fixture = (
        BlockchainTest(
            fork=Amsterdam,
            pre=deepcopy(pre),
            blocks=[Block(txs=[])],
            post={},
        )
        .generate(t8n=t8n, fixture_format=BlockchainFixture)
        .fixture
    )
    assert isinstance(probe_fixture, BlockchainFixture)
    probe_block = probe_fixture.blocks[0]
    assert isinstance(probe_block, FixtureBlock)
    extra_header = probe_block.header.rlp

    blocks = [Block(txs=[]) for _ in range(offset + 1)]
    blocks.append(
        Block(
            txs=[Transaction(sender=sender, to=contract, gas_limit=500_000)],
            expected_execution_witness_headers=(
                ExecutionWitnessHeadersExpectation(
                    expected_count=offset,
                ).modify(prepend_header(extra_header))
            ),
            expected_stateless_validation_success=True,
        )
    )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
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
