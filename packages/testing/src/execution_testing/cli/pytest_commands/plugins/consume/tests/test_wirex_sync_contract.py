"""
Tests for the wirex simulator's wire-coverage and client contracts.

Path resolution and its classification live in
`test_wirex_sync_targets`; this module covers what happens above a
resolved chain: which headers and bodies the per-hash coverage check
demands, and the identifiers isolating a multi-target fixture's
clients.
"""

from dataclasses import dataclass
from typing import cast

from execution_testing.base_types import Bytes, Hash
from execution_testing.devp2p.chain import Block, Chain
from execution_testing.fixtures.blockchain import FixtureHeader

from ..simulators.simulator_logic.test_via_wirex import (
    required_wire_bodies,
    required_wire_headers,
)
from ..simulators.wirex.client_policy import isolated_identifier


@dataclass
class _StubHeader:
    """The two header fields a served block is read by."""

    number: int
    block_hash: Hash


def _block(number: int, *, empty: bool) -> Block:
    """Return a block at `number`, with or without body content."""
    header = _StubHeader(number=number, block_hash=Hash(number))
    return Block(
        header=cast(FixtureHeader, header),
        transactions=[] if empty else [Bytes(b"\x01")],
        withdrawals=None,
    )


def _chain(blocks: list[Block]) -> Chain:
    """Return a chain of `blocks` under a stub genesis."""
    genesis = _StubHeader(number=0, block_hash=Hash(0))
    return Chain(genesis=cast(FixtureHeader, genesis), blocks=blocks)


class TestRequiredWireBodies:
    """Which bodies the wire-coverage check demands, per chain shape."""

    def test_the_announced_head_is_exempt(self) -> None:
        """
        A reth-shaped client passes: ancestors served, head never.

        The head's payload arrives through the Engine API, and whether
        a client also re-fetches its body from a peer goes both ways
        across measured clients - so the head is never required.
        """
        ancestors = [_block(1, empty=False), _block(2, empty=False)]
        chain = _chain([*ancestors, _block(3, empty=True)])
        required = required_wire_bodies(chain)
        assert required == ancestors
        served = {block.block_hash for block in ancestors}
        assert [b.number for b in required if b.block_hash not in served] == []

    def test_a_missing_ancestor_is_named(self) -> None:
        """An ancestor body that never traveled fails, by number."""
        chain = _chain(
            [
                _block(1, empty=False),
                _block(2, empty=False),
                _block(3, empty=True),
            ]
        )
        served = {_block(1, empty=False).block_hash}
        missing = [
            block.number
            for block in required_wire_bodies(chain)
            if block.block_hash not in served
        ]
        assert missing == [2]

    def test_derivable_ancestor_bodies_are_exempt(self) -> None:
        """An empty body a client derives from its header is not owed."""
        chain = _chain(
            [
                _block(1, empty=True),
                _block(2, empty=False),
                _block(3, empty=True),
            ]
        )
        assert [b.number for b in required_wire_bodies(chain)] == [2]

    def test_a_rejection_target_body_is_owed(self) -> None:
        """
        Below the target sits the block under judgement itself.

        An invalid path's target is the announced head, so the
        invalid block is an ancestor like any other: its non-derivable
        body is owed over the wire, which is what makes the client's
        verdict a judgement of blocks it fetched through its sync path.
        """
        chain = _chain([_block(1, empty=False), _block(2, empty=True)])
        assert [b.number for b in required_wire_bodies(chain)] == [1]


class TestRequiredWireHeaders:
    """Which headers the wire-coverage check demands."""

    def test_every_block_below_the_head_is_owed(self) -> None:
        """Empty body or not, a header can never be derived."""
        blocks = [
            _block(1, empty=True),
            _block(2, empty=False),
            _block(3, empty=True),
        ]
        assert required_wire_headers(_chain(blocks)) == blocks[:-1]

    def test_the_announced_head_is_exempt(self) -> None:
        """The head's payload arrives through the Engine API."""
        chain = _chain([_block(1, empty=False), _block(2, empty=False)])
        assert [b.number for b in required_wire_headers(chain)] == [1]


class TestIsolatedClientIdentifiers:
    """The keys a multi-target fixture's clients are managed under."""

    def test_the_suffix_is_the_targets_stable_position(self) -> None:
        """
        One identifier per target, derived from its announcement index.

        The suffix survives dropped siblings: a fixture whose first
        target is omitted still runs its second target as `-t1`, so
        logs and Hive artifacts name the same branch on every run.
        """
        group = "0xdeadbeef-go-ethereum"
        assert isolated_identifier(group, 0) == f"{group}-t0"
        assert isolated_identifier(group, 2) == f"{group}-t2"
