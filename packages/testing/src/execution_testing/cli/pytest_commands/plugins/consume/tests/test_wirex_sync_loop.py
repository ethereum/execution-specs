"""
Tests for the wirex test body's wait loops.

The Engine API and devp2p sides are replaced by small fakes and the
module's clock by a fake one, so a client that blocks an announcement
for minutes, or drops the peer mid-sync, is simulated in microseconds.
"""

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Callable, cast

import pytest

from execution_testing.base_types import Bytes, Hash
from execution_testing.devp2p.chain import Block, Chain
from execution_testing.devp2p.peer import MockPeer, PeerStatistics
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.rpc import EngineRPC, EthRPC
from execution_testing.rpc.rpc_types import PayloadStatus, PayloadStatusEnum

from ..simulators.helpers.exceptions import LoggedError
from ..simulators.helpers.timing import TimingData
from ..simulators.simulator_logic import test_via_wirex
from ..simulators.wirex.sync_targets import SyncTargetCase

SYNC_TIMEOUT = 30.0
ANNOUNCE_INTERVAL = 3.0
POLL_INTERVAL = 0.005


class FakeClock:
    """A monotonic clock that only moves when told to."""

    def __init__(self) -> None:
        """Start at zero."""
        self.now = 0.0

    def monotonic(self) -> float:
        """Return the current fake time."""
        return self.now

    def sleep(self, seconds: float) -> None:
        """Advance the fake time instead of sleeping."""
        self.now += seconds


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    """Replace the test body's clock with a fake one."""
    fake = FakeClock()
    monkeypatch.setattr(test_via_wirex, "time", fake)
    return fake


@dataclass
class _StubHeader:
    """The two header fields a served block is read by."""

    number: int
    block_hash: Hash


def _chain(length: int) -> Chain:
    """Return a chain of `length` non-empty blocks above a stub genesis."""
    genesis = _StubHeader(number=0, block_hash=Hash(0))
    blocks = [
        Block(
            header=cast(
                FixtureHeader, _StubHeader(number=n, block_hash=Hash(n))
            ),
            transactions=[Bytes(b"\x01")],
            withdrawals=None,
        )
        for n in range(1, length + 1)
    ]
    return Chain(genesis=cast(FixtureHeader, genesis), blocks=blocks)


def _case(chain: Chain, *, expects_rejection: bool) -> SyncTargetCase:
    """Return a single-target case announcing the head of `chain`."""
    target = SimpleNamespace(
        params=[SimpleNamespace(block_hash=chain.head.block_hash)],
        new_payload_version=4,
        forkchoice_updated_version=3,
        error_code=None,
    )
    return cast(
        SyncTargetCase,
        SimpleNamespace(
            chain=chain,
            target=target,
            expects_rejection=expects_rejection,
            announces_scaffolding=True,
            invalidities=set(),
            path=SimpleNamespace(total=1),
            name="target 0",
            label="target 0",
        ),
    )


def _status(status: PayloadStatusEnum) -> PayloadStatus:
    """Return a payload status carrying only `status`."""
    return PayloadStatus(
        status=status, latest_valid_hash=None, validation_error=None
    )


@dataclass
class FakeEngine:
    """
    An Engine API whose answers are functions of the fake time.

    `verdict` gives the `newPayload` answer at a time;
    `forkchoice_delay` gives how long the n-th `forkchoiceUpdated` of
    an announcement blocks.
    """

    clock: FakeClock
    verdict: Callable[[float], PayloadStatusEnum]
    forkchoice_delay: Callable[[int], float] = lambda _call: 0.0
    forkchoice_calls: int = 0

    def new_payload(self, *params: Any, version: int) -> PayloadStatus:
        """Answer with the verdict of this instant."""
        del params, version
        return _status(self.verdict(self.clock.now))

    def forkchoice_updated(self, **kwargs: Any) -> None:
        """Block for this call's delay."""
        del kwargs
        self.clock.now += self.forkchoice_delay(self.forkchoice_calls)
        self.forkchoice_calls += 1

    def forkchoice_updated_with_retry(self, **kwargs: Any) -> Any:
        """Confirm the head as canonical."""
        del kwargs
        return SimpleNamespace(payload_status=_status(PayloadStatusEnum.VALID))


@dataclass
class FakeEth:
    """An eth API whose head appears at `imported_at` fake seconds."""

    clock: FakeClock
    head_hash: str
    imported_at: float

    def get_block_by_hash(self, block_hash: Hash, full_txs: bool) -> Any:
        """Return the head once it has been imported."""
        del block_hash, full_txs
        if self.clock.now >= self.imported_at:
            return {"hash": self.head_hash}
        return None

    def get_block_by_number(self, number: str) -> Any:
        """Return the imported head as the latest block."""
        del number
        return {"hash": self.head_hash}


@dataclass
class FakePeer:
    """A peer that served every block of `chain` and stays connected."""

    chain: Chain
    alive: bool = True
    redials: int = 0
    statistics: PeerStatistics = field(default_factory=PeerStatistics)

    def __post_init__(self) -> None:
        """Record every block as served."""
        hashes = {block.block_hash for block in self.chain.blocks}
        self.header_hashes_ever_served = set(hashes)
        self.body_hashes_ever_served = set(hashes)

    def reconnect(self, chain: Chain) -> None:
        """Count a redial."""
        del chain
        self.redials += 1
        self.alive = True


def _run(
    case: SyncTargetCase, engine: FakeEngine, eth: FakeEth, peer: FakePeer
) -> None:
    """Run one target through the test body's loop."""
    test_via_wirex._run_sync_target(
        case=case,
        client=cast(Any, SimpleNamespace(id="client")),
        eth_rpc=cast(EthRPC, eth),
        engine_rpc=cast(EngineRPC, engine),
        mock_peer=cast(MockPeer, peer),
        timing_data=TimingData("Total"),
        genesis_verified_clients={"client"},
        genesis_header=cast(FixtureHeader, _StubHeader(0, Hash(0))),
        sync_timeout=SYNC_TIMEOUT,
        poll_interval=POLL_INTERVAL,
        announce_interval=ANNOUNCE_INTERVAL,
    )


class TestValidSyncDeadline:
    """The valid loop's last look at the head."""

    def test_a_blocking_reannouncement_does_not_hide_the_sync(
        self, clock: FakeClock
    ) -> None:
        """
        A re-announcement blocking far past the deadline is followed
        by one more look at the head, which the client imported while
        the call blocked.
        """
        chain = _chain(3)
        case = _case(chain, expects_rejection=False)
        engine = FakeEngine(
            clock,
            verdict=lambda _now: PayloadStatusEnum.SYNCING,
            forkchoice_delay=lambda call: 194.0 if call == 1 else 0.0,
        )
        eth = FakeEth(clock, "0x" + chain.head.block_hash.hex(), 100.0)
        _run(case, engine, eth, FakePeer(chain))
        assert clock.now > SYNC_TIMEOUT

    def test_a_head_never_imported_still_times_out(
        self, clock: FakeClock
    ) -> None:
        """The loop ends at the deadline when the head never appears."""
        chain = _chain(3)
        case = _case(chain, expects_rejection=False)
        engine = FakeEngine(
            clock, verdict=lambda _now: PayloadStatusEnum.SYNCING
        )
        eth = FakeEth(clock, "0x" + chain.head.block_hash.hex(), 1e9)
        with pytest.raises(LoggedError, match="never imported"):
            _run(case, engine, eth, FakePeer(chain))
        assert SYNC_TIMEOUT <= clock.now < SYNC_TIMEOUT + 1


class TestRejectionDeadline:
    """The rejection loop's verdict reading."""

    def test_a_blocking_reannouncement_does_not_hide_the_verdict(
        self, clock: FakeClock
    ) -> None:
        """
        A verdict formed while a re-announcement blocked past the
        deadline is still read: the loop asks once more before giving
        up.
        """
        chain = _chain(3)
        case = _case(chain, expects_rejection=True)
        engine = FakeEngine(
            clock,
            verdict=lambda now: (
                PayloadStatusEnum.INVALID
                if now >= 100.0
                else PayloadStatusEnum.SYNCING
            ),
            forkchoice_delay=lambda call: 194.0 if call == 1 else 0.0,
        )
        eth = FakeEth(clock, "0x" + chain.head.block_hash.hex(), 1e9)
        _run(case, engine, eth, FakePeer(chain))
        assert clock.now > SYNC_TIMEOUT

    def test_a_client_that_never_rejects_times_out(
        self, clock: FakeClock
    ) -> None:
        """The loop ends at the deadline when no verdict arrives."""
        chain = _chain(3)
        case = _case(chain, expects_rejection=True)
        engine = FakeEngine(
            clock, verdict=lambda _now: PayloadStatusEnum.SYNCING
        )
        eth = FakeEth(clock, "0x" + chain.head.block_hash.hex(), 1e9)
        with pytest.raises(LoggedError, match="never rejected"):
            _run(case, engine, eth, FakePeer(chain))
        assert SYNC_TIMEOUT <= clock.now < SYNC_TIMEOUT + 1

    def test_a_held_acceptance_fails(self, clock: FakeClock) -> None:
        """A VALID that holds for the acceptance hold time fails."""
        chain = _chain(3)
        case = _case(chain, expects_rejection=True)
        engine = FakeEngine(
            clock, verdict=lambda _now: PayloadStatusEnum.VALID
        )
        eth = FakeEth(clock, "0x" + chain.head.block_hash.hex(), 1e9)
        with pytest.raises(LoggedError, match="accepted the invalid chain"):
            _run(case, engine, eth, FakePeer(chain))
        assert clock.now < test_via_wirex.ACCEPTANCE_HOLD_TIME + 1
