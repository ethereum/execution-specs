"""Test suite for ``_split_setup_blocks_by_gas`` in stateful filling."""

import pytest

from execution_testing.test_types import TestPhase, Transaction

from ..blockchain import (
    _SETUP_BLOCK_GAS_HEADROOM,
    Block,
    _split_setup_blocks_by_gas,
)

BLOCK_GAS_LIMIT = 1_000_000
"""Stand-in for the snapshot chain's block gas limit."""

BUDGET = int(BLOCK_GAS_LIMIT * _SETUP_BLOCK_GAS_HEADROOM)


def _tx(
    gas_limit: int, phase: TestPhase | None = TestPhase.SETUP
) -> Transaction:
    """Build a phase-tagged Transaction of the given gas limit."""
    tx = Transaction(gas_limit=gas_limit)
    tx.test_phase = phase
    return tx


def _split(block: Block) -> list[Block]:
    """Split *block* against the stand-in block gas limit."""
    return _split_setup_blocks_by_gas([block], block_gas_limit=BLOCK_GAS_LIMIT)


def test_passthrough_within_budget() -> None:
    """A setup block that already fits is returned unchanged."""
    block = Block(txs=[_tx(100_000) for _ in range(5)])
    out = _split(block)
    assert len(out) == 1
    assert out[0] is block


def test_passthrough_empty() -> None:
    """Empty-txs block is returned unchanged (identity)."""
    block = Block(txs=[])
    out = _split(block)
    assert len(out) == 1
    assert out[0] is block


def test_passthrough_all_untagged() -> None:
    """Block with no phase-tagged txs is returned unchanged."""
    block = Block(txs=[_tx(BLOCK_GAS_LIMIT, phase=None) for _ in range(4)])
    out = _split(block)
    assert len(out) == 1
    assert out[0] is block


def test_execution_block_never_split() -> None:
    """Execution block survives intact far past the block gas limit."""
    block = Block(
        txs=[
            _tx(BLOCK_GAS_LIMIT, phase=TestPhase.EXECUTION) for _ in range(10)
        ]
    )
    out = _split(block)
    assert len(out) == 1
    assert out[0] is block


def test_every_sub_block_fits_the_budget() -> None:
    """Over-budget setup work spans blocks that each fit."""
    out = _split(Block(txs=[_tx(200_000) for _ in range(25)]))
    assert len(out) > 1
    for block in out:
        assert sum(tx.gas_limit for tx in block.txs) <= BUDGET


def test_split_preserves_every_tx_in_order() -> None:
    """Splitting neither drops, duplicates nor reorders transactions."""
    txs = [_tx(200_000) for _ in range(25)]
    out = _split(Block(txs=txs))
    assert [tx for block in out for tx in block.txs] == txs


def test_tx_at_the_limit_gets_its_own_block() -> None:
    """A tx past the budget but within the limit is isolated, not dropped."""
    first, huge, last = _tx(21_000), _tx(BLOCK_GAS_LIMIT), _tx(21_000)
    out = _split(Block(txs=[first, huge, last]))
    assert [len(block.txs) for block in out] == [1, 1, 1]
    assert out[0].txs[0] is first
    assert out[1].txs[0] is huge
    assert out[2].txs[0] is last


def test_tx_past_the_limit_raises() -> None:
    """A tx no block can hold fails loudly instead of being emitted."""
    block = Block(txs=[_tx(21_000), _tx(BLOCK_GAS_LIMIT * 3)])
    with pytest.raises(ValueError, match="no split can make it fit"):
        _split(block)


@pytest.mark.parametrize(
    "gas_limits, expected_sizes",
    [
        ([500_000, 400_000], [2]),
        ([500_000, 600_000], [1, 1]),
        ([900_000, 90_000], [2]),
        ([900_000, 100_000], [1, 1]),
        ([250_000] * 9, [3, 3, 3]),
        ([300_000] * 7, [3, 3, 1]),
        ([BLOCK_GAS_LIMIT // 2] * 2, [1, 1]),
    ],
)
def test_sub_block_sizes(
    gas_limits: list[int], expected_sizes: list[int]
) -> None:
    """Sub-block sizes follow a greedy pack of the gas budget."""
    block = Block(txs=[_tx(gas) for gas in gas_limits])
    out = _split(block)
    assert [len(block.txs) for block in out] == expected_sizes
