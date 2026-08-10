"""Tests for the wirex simulator's per-class sync-block contract."""

from dataclasses import dataclass
from typing import cast

from execution_testing.base_types import Bytes, Hash
from execution_testing.devp2p.chain import Block, Chain
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureHeader,
)

from ..simulators.simulator_logic.test_via_wirex import (
    announced_payload,
    required_wire_bodies,
)
from ..simulators.wirex.conftest import sync_chain_payloads


def _payload() -> FixtureEngineNewPayload:
    """Return a bare payload sentinel; the tests read identity only."""
    return cast(FixtureEngineNewPayload, object())


@dataclass
class _StubFixture:
    """The two fixture fields the contract helpers read."""

    payloads: list[FixtureEngineNewPayload]
    sync_payload: FixtureEngineNewPayload | None


def _fixture(
    payloads: list[FixtureEngineNewPayload],
    sync_payload: FixtureEngineNewPayload | None = None,
) -> BlockchainEngineXFixture:
    """Return a fixture carrying exactly the fields the helpers read."""
    return cast(BlockchainEngineXFixture, _StubFixture(payloads, sync_payload))


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


class TestAnnouncedPayload:
    """Which block the simulator announces, per chain class."""

    def test_appended_class_announces_the_trailer(self) -> None:
        """A fixture with a sync payload announces it, not its head."""
        test_block, trailer = _payload(), _payload()
        assert announced_payload(_fixture([test_block], trailer)) is trailer

    def test_prepended_class_announces_its_own_head(self) -> None:
        """An in-chain prepend keeps the test's block as the target."""
        prepended, invalid_head = _payload(), _payload()
        fixture = _fixture([prepended, invalid_head])
        assert announced_payload(fixture) is invalid_head

    def test_bare_chain_announces_its_own_head(self) -> None:
        """A chain with no extra block announces the author's head."""
        first, head = _payload(), _payload()
        assert announced_payload(_fixture([first, head])) is head


class TestSyncChainPayloads:
    """The served sequence, and the chain length skips are judged by."""

    def test_appended_singleton_becomes_two_blocks(self) -> None:
        """The trailer joins the served chain, above the test's head."""
        test_block, trailer = _payload(), _payload()
        payloads = sync_chain_payloads(_fixture([test_block], trailer))
        assert payloads == [test_block, trailer]

    def test_prepended_singleton_is_already_two_blocks(self) -> None:
        """An in-chain prepend needs no assembly."""
        prepended, invalid_head = _payload(), _payload()
        fixture = _fixture([prepended, invalid_head])
        assert sync_chain_payloads(fixture) == [prepended, invalid_head]

    def test_bare_singleton_stays_one_block(self) -> None:
        """No extra block, nothing to add: skipped below the minimum."""
        assert len(sync_chain_payloads(_fixture([_payload()]))) == 1

    def test_bare_chain_keeps_its_own_length(self) -> None:
        """An invalid multi-block chain is served exactly as written."""
        payloads = [_payload(), _payload()]
        assert sync_chain_payloads(_fixture(payloads)) == payloads

    def test_the_author_payload_list_is_not_mutated(self) -> None:
        """Assembly returns a new list; the fixture stays the author's."""
        test_block, trailer = _payload(), _payload()
        fixture = _fixture([test_block], trailer)
        sync_chain_payloads(fixture)
        assert fixture.payloads == [test_block]


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

    def test_prepend_class_check_is_vacuous(self) -> None:
        """
        Below an invalid head sits only the empty prepended block.

        Its body is derivable, so nothing is owed over the wire - the
        test's own block is judged through the Engine API instead.
        """
        chain = _chain([_block(1, empty=True), _block(2, empty=False)])
        assert required_wire_bodies(chain) == []
