"""Test suite for ``_split_blocks_by_phase`` in stateful filling."""

import pytest

from execution_testing.test_types import TestPhase, Transaction
from execution_testing.test_types.transaction_types import (
    TransactionTestMetadata,
)

from ..blockchain import Block, _split_blocks_by_phase, _tx_phase


def _tx(phase: TestPhase | None) -> Transaction:
    """Build a Transaction tagged with the given test_phase."""
    tx = Transaction()
    tx.test_phase = phase
    return tx


def _phases_of(block: Block) -> list[TestPhase | None]:
    """Return the per-tx phase list for *block*."""
    return [_tx_phase(tx) for tx in block.txs]


def test_passthrough_pure_setup() -> None:
    """Pure-SETUP block is returned unchanged (identity)."""
    block = Block(txs=[_tx(TestPhase.SETUP), _tx(TestPhase.SETUP)])
    out = _split_blocks_by_phase([block])
    assert len(out) == 1
    assert out[0] is block


def test_passthrough_pure_execution() -> None:
    """Pure-EXECUTION block is returned unchanged (identity)."""
    block = Block(txs=[_tx(TestPhase.EXECUTION), _tx(TestPhase.EXECUTION)])
    out = _split_blocks_by_phase([block])
    assert len(out) == 1
    assert out[0] is block


def test_passthrough_empty() -> None:
    """Empty-txs block is returned unchanged (identity)."""
    block = Block(txs=[])
    out = _split_blocks_by_phase([block])
    assert len(out) == 1
    assert out[0] is block


def test_passthrough_all_untagged() -> None:
    """Block with no phase-tagged txs is returned unchanged."""
    block = Block(txs=[_tx(None), _tx(None)])
    out = _split_blocks_by_phase([block])
    assert len(out) == 1
    assert out[0] is block


def test_split_setup_then_execution() -> None:
    """[S, S, E, E] splits into pure-SETUP then pure-EXECUTION blocks."""
    block = Block(
        txs=[
            _tx(TestPhase.SETUP),
            _tx(TestPhase.SETUP),
            _tx(TestPhase.EXECUTION),
            _tx(TestPhase.EXECUTION),
        ]
    )
    out = _split_blocks_by_phase([block])
    assert [_phases_of(b) for b in out] == [
        [TestPhase.SETUP, TestPhase.SETUP],
        [TestPhase.EXECUTION, TestPhase.EXECUTION],
    ]


def test_split_preserves_interleaved_order() -> None:
    """[E, S, E] splits into 3 sub-blocks, original tx order preserved."""
    block = Block(
        txs=[
            _tx(TestPhase.EXECUTION),
            _tx(TestPhase.SETUP),
            _tx(TestPhase.EXECUTION),
        ]
    )
    out = _split_blocks_by_phase([block])
    assert [_phases_of(b) for b in out] == [
        [TestPhase.EXECUTION],
        [TestPhase.SETUP],
        [TestPhase.EXECUTION],
    ]


def test_split_clears_intermediate_block_fields() -> None:
    """
    Block-level "expected" fields apply only to the final post-state of
    the original block, so they stay on the LAST sub-block; preceding
    sub-blocks get them cleared.
    """
    expected_gas_used = 12345
    block = Block(
        txs=[_tx(TestPhase.SETUP), _tx(TestPhase.EXECUTION)],
        expected_gas_used=expected_gas_used,
    )
    out = _split_blocks_by_phase([block])
    assert len(out) == 2
    assert out[0].expected_gas_used is None
    assert out[1].expected_gas_used == expected_gas_used


def test_split_mixed_with_untagged_phases() -> None:
    """Untagged txs (phase ``None``) form their own contiguous run."""
    block = Block(
        txs=[_tx(TestPhase.SETUP), _tx(None), _tx(TestPhase.EXECUTION)]
    )
    out = _split_blocks_by_phase([block])
    assert [_phases_of(b) for b in out] == [
        [TestPhase.SETUP],
        [None],
        [TestPhase.EXECUTION],
    ]


def test_metadata_phase_fallback() -> None:
    """
    When ``tx.test_phase`` is unset, ``tx.metadata.phase`` is used as
    fallback (matches ``FixtureEngineNewPayload.derive_phase`` rules).
    """
    tx_setup = Transaction()
    tx_setup.metadata = TransactionTestMetadata(phase=TestPhase.SETUP)
    tx_exec = Transaction()
    tx_exec.test_phase = TestPhase.EXECUTION

    block = Block(txs=[tx_setup, tx_exec])
    out = _split_blocks_by_phase([block])
    assert [_phases_of(b) for b in out] == [
        [TestPhase.SETUP],
        [TestPhase.EXECUTION],
    ]


@pytest.mark.parametrize(
    "phases, expected_sizes",
    [
        ([TestPhase.SETUP] * 3, [3]),
        ([TestPhase.SETUP, TestPhase.EXECUTION], [1, 1]),
        ([TestPhase.SETUP, TestPhase.SETUP, TestPhase.EXECUTION], [2, 1]),
        (
            [TestPhase.EXECUTION, TestPhase.SETUP, TestPhase.EXECUTION],
            [1, 1, 1],
        ),
    ],
)
def test_sub_block_sizes(
    phases: list[TestPhase], expected_sizes: list[int]
) -> None:
    """Sub-block sizes match the per-phase contiguous-run partition."""
    block = Block(txs=[_tx(p) for p in phases])
    out = _split_blocks_by_phase([block])
    assert [len(b.txs) for b in out] == expected_sizes
