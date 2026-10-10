"""
Tests [EIP-7709: Read BLOCKHASH from storage and update cost](https://eips.ethereum.org/EIPS/eip-7709).

Test the correctness of the BLOCKHASH opcode when reading from the
EIP-2935 history storage contract.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    CodeGasMeasure,
    Fork,
    Op,
    Storage,
    Transaction,
)

from .helpers import HISTORY_RET_OFFSET, history_staticcall
from .spec import Spec, ref_spec_7709

REFERENCE_SPEC_GIT_PATH = ref_spec_7709.git_path
REFERENCE_SPEC_VERSION = ref_spec_7709.version

pytestmark = pytest.mark.valid_from("EIP7709")


def test_blockhash_valid_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that `BLOCKHASH` returns the history contract's hash for a block
    whose slot an earlier block's system call wrote.
    """
    storage = Storage()

    query_block = 1
    code = (
        # Check that the history contract call succeeds and writes the
        # reference block hash to memory.
        Op.SSTORE(
            storage.store_next(True),
            history_staticcall(query_block),
        )
        # Check that BLOCKHASH returns the same value as the history contract.
        + Op.SSTORE(
            storage.store_next(True),
            Op.EQ(
                Op.BLOCKHASH(query_block),
                Op.MLOAD(HISTORY_RET_OFFSET),
            ),
        )
        # Check that a valid ancestor still returns a non-zero block hash.
        + Op.SSTORE(
            storage.store_next(False),
            Op.ISZERO(Op.BLOCKHASH(query_block)),
        )
    )

    contract = pre.deploy_contract(code, storage=storage.canary())
    blocks = [
        Block(),
        # This block's system call writes block 1's slot.
        Block(),
        Block(txs=[Transaction(to=contract, sender=pre.fund_eoa())]),
    ]
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={contract: Account(storage=storage)},
    )


@pytest.mark.parametrize(
    "block_number",
    [
        pytest.param(Op.NUMBER, id="current_block"),
        pytest.param(Op.ADD(Op.NUMBER, 1), id="next_block"),
        pytest.param(
            # Shares block 1's populated history slot.
            1 + Spec.HISTORY_SERVE_WINDOW,
            id="aliased_future_block",
        ),
    ],
)
def test_blockhash_unavailable_block_is_zero(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    block_number: int | Bytecode,
) -> None:
    """
    Test that `BLOCKHASH` returns zero for a block not yet on the chain,
    even when its history slot holds another block's hash.
    """
    storage = Storage()

    code = Op.SSTORE(storage.store_next(0), Op.BLOCKHASH(block_number))

    contract = pre.deploy_contract(code, storage=storage.canary())
    blocks = [
        Block(),
        # This block's system call writes block 1's slot.
        Block(txs=[Transaction(to=contract, sender=pre.fund_eoa())]),
    ]
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={contract: Account(storage=storage)},
    )


@pytest.mark.parametrize(
    "block_offset,in_window",
    [
        pytest.param(
            Spec.BLOCKHASH_SERVE_WINDOW,
            True,
            id="oldest_in_window",
        ),
        pytest.param(
            Spec.BLOCKHASH_SERVE_WINDOW + 1,
            False,
            id="newest_out_of_window",
        ),
    ],
)
@pytest.mark.slow()
def test_blockhash_serve_window_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    block_offset: int,
    in_window: bool,
) -> None:
    """
    Test that `BLOCKHASH` returns the hash of a block, and charges for its
    history slot, only while the block lies within the serve window, even
    though the history contract still holds the hash after it leaves.
    """
    storage = Storage()

    query_block = 1
    measured = Op.BLOCKHASH(query_block, in_window=in_window)
    expected_hash = Op.MLOAD(HISTORY_RET_OFFSET) if in_window else 0
    code = (
        # Measure first: the history call below warms the slot.
        CodeGasMeasure(
            code=measured,
            extra_stack_items=1,
            sstore_key=storage.store_next(measured.gas_cost(fork)),
        )
        # Check that the history contract call succeeds and writes the
        # reference block hash to memory.
        + Op.SSTORE(
            storage.store_next(True),
            history_staticcall(query_block),
        )
        # Check that the history contract still serves a non-zero hash.
        + Op.SSTORE(
            storage.store_next(False),
            Op.ISZERO(Op.MLOAD(HISTORY_RET_OFFSET)),
        )
        # Check that BLOCKHASH returns the history hash only in window.
        + Op.SSTORE(
            storage.store_next(True),
            Op.EQ(Op.BLOCKHASH(query_block), expected_hash),
        )
    )

    contract = pre.deploy_contract(code, storage=storage.canary())
    blocks = [Block() for _ in range(block_offset)]
    blocks.append(Block(txs=[Transaction(to=contract, sender=pre.fund_eoa())]))
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={contract: Account(storage=storage)},
    )
