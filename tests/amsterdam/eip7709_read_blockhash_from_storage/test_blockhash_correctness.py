"""
Tests [EIP-7709: Read BLOCKHASH from storage and update cost](https://eips.ethereum.org/EIPS/eip-7709).

Test the correctness of the BLOCKHASH opcode when reading from the
EIP-2935 history storage contract.
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Op,
    Storage,
    Transaction,
)

from .spec import Spec, ref_spec_7709

REFERENCE_SPEC_GIT_PATH = ref_spec_7709.git_path
REFERENCE_SPEC_VERSION = ref_spec_7709.version

pytestmark = pytest.mark.valid_from("Amsterdam")

HISTORY_RET_OFFSET = 32


def history_staticcall(query_block: int) -> Bytecode:
    """Return bytecode that queries the history contract for a block hash."""
    return Op.MSTORE(0, query_block) + Op.STATICCALL(
        Op.GAS,
        Spec.HISTORY_STORAGE_ADDRESS,
        0,
        32,
        HISTORY_RET_OFFSET,
        32,
    )


@pytest.mark.parametrize(
    "block_offset",
    [
        pytest.param(1, id="previous_block"),
        pytest.param(2, id="two_blocks_ago"),
    ],
)
def test_blockhash_valid_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    block_offset: int,
) -> None:
    """
    Test that BLOCKHASH(1) matches the history contract and returns
    a non-zero value when block 1 is one or two blocks behind the
    executing block.
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

    contract_address = pre.deploy_contract(code)
    sender = pre.fund_eoa()

    blocks = [Block() for _ in range(block_offset)]
    blocks.append(
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        )
    )

    post: Dict[Address, Account] = {
        contract_address: Account(storage=storage),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_blockhash_current_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that BLOCKHASH returns zero when querying the current block
    number.
    """
    storage = Storage()

    code = Op.SSTORE(
        storage.store_next(True),
        Op.ISZERO(Op.BLOCKHASH(Op.NUMBER)),
    )

    contract_address = pre.deploy_contract(code)
    sender = pre.fund_eoa()

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        )
    ]

    post: Dict[Address, Account] = {
        contract_address: Account(storage=storage),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_blockhash_future_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that BLOCKHASH returns zero when querying a future block number.
    """
    storage = Storage()

    code = Op.SSTORE(
        storage.store_next(True),
        Op.ISZERO(Op.BLOCKHASH(2)),
    )

    contract_address = pre.deploy_contract(code)
    sender = pre.fund_eoa()

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        )
    ]

    post: Dict[Address, Account] = {
        contract_address: Account(storage=storage),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.parametrize(
    "block_offset,expect_equal",
    [
        pytest.param(
            Spec.BLOCKHASH_SERVE_WINDOW,
            True,
            id="last_valid_block",
        ),
        pytest.param(
            Spec.BLOCKHASH_SERVE_WINDOW + 1,
            False,
            id="first_invalid_block",
        ),
    ],
)
@pytest.mark.slow()
def test_blockhash_boundary_256(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    block_offset: int,
    expect_equal: bool,
) -> None:
    """
    Test the 256-block BLOCKHASH window boundary for block 1.

    When block 1 is `N - 256`, `BLOCKHASH(1)` must equal the history
    contract and be non-zero. When block 1 is `N - 257`, `BLOCKHASH(1)`
    must be zero even though the history contract still returns the
    stored hash.
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
        # Check that the history contract still serves a non-zero hash here.
        + Op.SSTORE(
            storage.store_next(False),
            Op.ISZERO(Op.MLOAD(HISTORY_RET_OFFSET)),
        )
        # Check that BLOCKHASH becomes zero only after the 256-block window.
        + Op.SSTORE(
            storage.store_next(not expect_equal),
            Op.ISZERO(Op.BLOCKHASH(query_block)),
        )
        # Check that BLOCKHASH matches history only on the last valid case.
        + Op.SSTORE(
            storage.store_next(expect_equal),
            Op.EQ(
                Op.BLOCKHASH(query_block),
                Op.MLOAD(HISTORY_RET_OFFSET),
            ),
        )
    )

    contract_address = pre.deploy_contract(code)
    sender = pre.fund_eoa()

    blocks = [Block() for _ in range(block_offset)]
    blocks.append(
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        )
    )

    post: Dict[Address, Account] = {
        contract_address: Account(storage=storage),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)
