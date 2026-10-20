"""
Tests for the wirex test body's wait loops.

The Engine API and devp2p sides are replaced by small fakes and the
module's clock by a fake one, so a client that blocks an announcement
for minutes, or drops the peer mid-sync, is simulated in microseconds.
"""

import inspect
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from itertools import pairwise
from types import SimpleNamespace
from typing import Any, Callable, Collection, Iterator, cast

import pytest
from tenacity import RetryCallState

from execution_testing.base_types import Address, Bytes, Hash
from execution_testing.devp2p.chain import Block, Chain
from execution_testing.devp2p.peer import MockPeer, PeerStatistics
from execution_testing.devp2p.rlpx import RLPxError
from execution_testing.exceptions import BlockException
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureHeader,
)
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    ForkchoiceUpdateTimeoutError,
)
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    ForkchoiceUpdateResponse,
    JSONRPCError,
    PayloadAttributes,
    PayloadStatus,
    PayloadStatusEnum,
)

from ..simulators.helpers.exceptions import (
    GenesisBlockMismatchExceptionError,
    LoggedError,
)
from ..simulators.helpers.timing import TimingData
from ..simulators.simulator_logic import test_via_wirex
from ..simulators.wirex.sync_targets import SyncPath, SyncTargetCase

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


FIRST_INVALID_PARENT = Hash(1)
"""
The hash a rejection of a stub chain owes by default: the chain's head
is a sync target and the block below it is the first invalid one.
"""


def _case(
    chain: Chain,
    *,
    expects_rejection: bool,
    announces_scaffolding: bool = True,
    invalidities: frozenset[Any] = frozenset(),
    error_code: int | None = None,
    expected_latest_valid_hash: Hash | None = FIRST_INVALID_PARENT,
    index: int = 0,
    total: int = 1,
) -> SyncTargetCase:
    """
    Return a case announcing the head of `chain`.

    A rejection owes `expected_latest_valid_hash` as its
    `latestValidHash`.
    """
    target = SimpleNamespace(
        params=[SimpleNamespace(block_hash=chain.head.block_hash)],
        new_payload_version=4,
        forkchoice_updated_version=3,
        error_code=error_code,
    )
    path = SimpleNamespace(
        target=target,
        expects_rejection=expects_rejection,
        announces_scaffolding=announces_scaffolding,
        invalidities=set(invalidities),
        expected_latest_valid_hash=expected_latest_valid_hash,
        total=total,
        name=f"target {index}",
        label=f"target {index}",
    )
    return SyncTargetCase(path=cast(SyncPath, path), chain=chain)


def _status(
    status: PayloadStatusEnum, latest_valid_hash: Hash | None = None
) -> PayloadStatus:
    """Return a payload status carrying `status` and no reason."""
    return PayloadStatus(
        status=status,
        latest_valid_hash=latest_valid_hash,
        validation_error=None,
    )


def _response(status: PayloadStatusEnum) -> ForkchoiceUpdateResponse:
    """Return a forkchoice response carrying only `status`."""
    return ForkchoiceUpdateResponse(
        payload_status=_status(status), payload_id=None
    )


@dataclass
class FakeEngine:
    """
    An Engine API whose answers are functions of the fake time.

    `verdict` gives the `newPayload` answer at a time and `refusal` the
    error code it raises instead, if any; `forkchoice_delay` gives how
    long the n-th `forkchoiceUpdated` of an announcement blocks and
    `forkchoice_refusal` the error code it raises; `confirmation` is
    the answer, or the exception, of the confirming update.
    `latest_valid_hash` comes with every `newPayload` answer.
    """

    clock: FakeClock
    verdict: Callable[[float], PayloadStatusEnum]
    forkchoice_delay: Callable[[int], float] = lambda _call: 0.0
    refusal: Callable[[float], int | None] = lambda _now: None
    forkchoice_refusal: Callable[[int], int | None] = lambda _call: None
    confirmation: PayloadStatusEnum | Exception = PayloadStatusEnum.VALID
    latest_valid_hash: Hash | None = None
    forkchoice_calls: int = 0

    def new_payload(self, *params: Any, version: int) -> PayloadStatus:
        """Answer with the verdict of this instant, or refuse."""
        del params, version
        code = self.refusal(self.clock.now)
        if code is not None:
            raise JSONRPCError(code, "refused")
        return _status(self.verdict(self.clock.now), self.latest_valid_hash)

    def forkchoice_updated(
        self,
        forkchoice_state: ForkchoiceState,
        payload_attributes: PayloadAttributes | None = None,
        *,
        version: int,
    ) -> ForkchoiceUpdateResponse:
        """Block for this call's delay, then accept or refuse."""
        del forkchoice_state, payload_attributes, version
        call = self.forkchoice_calls
        self.clock.now += self.forkchoice_delay(call)
        self.forkchoice_calls += 1
        code = self.forkchoice_refusal(call)
        if code is not None:
            raise JSONRPCError(code, "refused")
        return _response(PayloadStatusEnum.SYNCING)

    def forkchoice_updated_with_retry(
        self,
        forkchoice_state: ForkchoiceState,
        forkchoice_version: int,
        *,
        max_attempts: int = 30,
        wait_fixed: float = 1.0,
        on_retry: Callable[[RetryCallState], None] | None = None,
    ) -> ForkchoiceUpdateResponse:
        """Confirm the head with the configured answer."""
        del forkchoice_state, forkchoice_version, max_attempts
        del wait_fixed, on_retry
        if isinstance(self.confirmation, Exception):
            raise self.confirmation
        return _response(self.confirmation)


GENESIS_HASH = Hash(0)


@dataclass
class FakeEth:
    """
    An eth API whose head appears at `imported_at` fake seconds.

    `overrides` replaces the answer for a block number, so a test can
    serve a wrong or missing genesis or latest block.
    """

    clock: FakeClock
    head_hash: str
    imported_at: float
    overrides: dict[int | str, Any] = field(default_factory=dict)

    def get_block_by_hash(
        self, block_hash: Hash, full_txs: bool = True
    ) -> Any:
        """Return the head once it has been imported."""
        del block_hash, full_txs
        if self.clock.now >= self.imported_at:
            return {"hash": self.head_hash}
        return None

    def get_block_by_number(
        self, block_number: int | str = "latest", full_txs: bool = True
    ) -> Any:
        """Return genesis for 0 and the imported head otherwise."""
        del full_txs
        if block_number in self.overrides:
            return self.overrides[block_number]
        if block_number == 0:
            return {"hash": str(GENESIS_HASH)}
        return {"hash": self.head_hash}


@dataclass
class FakePeer:
    """
    A peer that served every block of `chain` and stays connected.

    The headers and bodies of the blocks numbered in `unserved_headers`
    and `unserved_bodies` never traveled.
    """

    chain: Chain
    unserved_headers: Collection[int] = ()
    unserved_bodies: Collection[int] = ()
    alive: bool = True
    redials: int = 0
    disconnect_reason: int | None = None
    statistics: PeerStatistics = field(default_factory=PeerStatistics)

    def __post_init__(self) -> None:
        """Record every block as served, bar the unserved ones."""
        blocks = self.chain.blocks
        self.header_hashes_ever_served = {
            b.block_hash
            for b in blocks
            if b.number not in self.unserved_headers
        }
        self.body_hashes_ever_served = {
            b.block_hash
            for b in blocks
            if b.number not in self.unserved_bodies
        }

    def reconnect(self, chain: Chain, timeout: float = 30.0) -> None:
        """Count a redial."""
        del chain, timeout
        self.redials += 1
        self.alive = True


def _head(chain: Chain) -> str:
    """Return the hex hash `eth` answers for the head of `chain`."""
    return str(chain.head.block_hash)


CHAIN = _chain(3)
"""The chain every single-target test serves and announces."""

NEVER = 1e9
"""An import time no test reaches."""


def _engine(
    clock: FakeClock,
    verdict: PayloadStatusEnum | Callable[[float], PayloadStatusEnum] = (
        PayloadStatusEnum.SYNCING
    ),
    **knobs: Any,
) -> FakeEngine:
    """Return an engine answering `verdict`, fixed or a function of time."""
    if isinstance(verdict, PayloadStatusEnum):
        fixed = verdict
        return FakeEngine(clock, verdict=lambda _now: fixed, **knobs)
    return FakeEngine(clock, verdict=verdict, **knobs)


def _run(
    clock: FakeClock,
    engine: FakeEngine,
    *,
    expects_rejection: bool = False,
    imported_at: float = NEVER,
    peer: FakePeer | None = None,
    overrides: dict[int | str, Any] | None = None,
    genesis_header: FixtureHeader | None = None,
    **case_knobs: Any,
) -> None:
    """
    Run `CHAIN` through the test body's loop against the fakes.

    The head is imported at `imported_at`, and genesis is checked only
    when `genesis_header` is given.
    """
    verified = {"client"}
    if genesis_header is None:
        genesis_header = cast(FixtureHeader, _StubHeader(0, GENESIS_HASH))
    else:
        verified = set()
    eth = FakeEth(clock, _head(CHAIN), imported_at, overrides or {})
    test_via_wirex._run_sync_target(
        case=_case(CHAIN, expects_rejection=expects_rejection, **case_knobs),
        client=cast(Any, SimpleNamespace(id="client")),
        eth_rpc=cast(EthRPC, eth),
        engine_rpc=cast(EngineRPC, engine),
        mock_peer=cast(MockPeer, peer or FakePeer(CHAIN)),
        timing_data=TimingData("Total"),
        genesis_verified_clients=verified,
        genesis_header=genesis_header,
        sync_timeout=SYNC_TIMEOUT,
        poll_interval=POLL_INTERVAL,
        announce_interval=ANNOUNCE_INTERVAL,
    )


FAKE_SIGNATURES = [
    (FakeEngine.new_payload, EngineRPC.new_payload),
    (FakeEngine.forkchoice_updated, EngineRPC.forkchoice_updated),
    (
        FakeEngine.forkchoice_updated_with_retry,
        EngineRPC.forkchoice_updated_with_retry,
    ),
    (FakeEth.get_block_by_hash, EthRPC.get_block_by_hash),
    (FakeEth.get_block_by_number, EthRPC.get_block_by_number),
    (FakePeer.reconnect, MockPeer.reconnect),
]


class TestFakeFidelity:
    """The fakes stand in for the real APIs the test body calls."""

    @pytest.mark.parametrize(
        "fake,real",
        FAKE_SIGNATURES,
        ids=[fake.__qualname__ for fake, _ in FAKE_SIGNATURES],
    )
    def test_a_fake_accepts_only_calls_the_real_method_accepts(
        self, fake: Callable[..., Any], real: Callable[..., Any]
    ) -> None:
        """Fake parameters are real ones of the same kind, none missing."""
        fake_parameters = inspect.signature(fake).parameters
        real_parameters = inspect.signature(real).parameters
        for name, parameter in fake_parameters.items():
            assert name in real_parameters, f"{name} is not a real parameter"
            assert parameter.kind == real_parameters[name].kind, name
        for name, parameter in real_parameters.items():
            required = parameter.default is inspect.Parameter.empty
            variadic = parameter.kind in (
                parameter.VAR_POSITIONAL,
                parameter.VAR_KEYWORD,
            )
            if required and not variadic:
                assert name in fake_parameters, f"{name} is required"


VALID = PayloadStatusEnum.VALID
INVALID = PayloadStatusEnum.INVALID
SYNCING = PayloadStatusEnum.SYNCING


@pytest.mark.parametrize(
    "expects_rejection", [False, True], ids=["sync", "rejection"]
)
class TestDeadline:
    """Both wait loops read the client once more before giving up."""

    def test_a_blocking_reannouncement_hides_nothing(
        self, clock: FakeClock, expects_rejection: bool
    ) -> None:
        """A head imported or rejected during a blocked call is still read."""
        engine = _engine(
            clock,
            lambda now: INVALID if now >= 100.0 else SYNCING,
            forkchoice_delay=lambda call: 194.0 if call == 1 else 0.0,
        )
        _run(
            clock,
            engine,
            expects_rejection=expects_rejection,
            imported_at=100.0,
        )
        assert clock.now > SYNC_TIMEOUT

    def test_a_silent_client_times_out(
        self, clock: FakeClock, expects_rejection: bool
    ) -> None:
        """A client that never imports nor rejects fails at the deadline."""
        never = "never rejected" if expects_rejection else "never imported"
        with pytest.raises(LoggedError, match=never):
            _run(clock, _engine(clock), expects_rejection=expects_rejection)
        assert SYNC_TIMEOUT <= clock.now < SYNC_TIMEOUT + 1


class TestAcceptanceHold:
    """A VALID verdict on an invalid head fails only once it has held."""

    def test_a_held_acceptance_fails(self, clock: FakeClock) -> None:
        """A VALID that holds for half a second fails there and then."""
        with pytest.raises(LoggedError, match="accepted the invalid chain"):
            _run(clock, _engine(clock, VALID), expects_rejection=True)
        assert 0.5 <= clock.now < 0.6

    def test_a_transient_acceptance_then_rejection_passes(
        self, clock: FakeClock
    ) -> None:
        """A VALID that turns INVALID within the hold is no acceptance."""
        engine = _engine(clock, lambda now: VALID if now < 0.3 else INVALID)
        _run(clock, engine, expects_rejection=True)

    def test_an_acceptance_interrupted_by_syncing_restarts_the_hold(
        self, clock: FakeClock
    ) -> None:
        """VALID flapping with SYNCING, each under the hold, never fails."""
        engine = _engine(
            clock, lambda now: VALID if now % 0.6 < 0.3 else SYNCING
        )
        with pytest.raises(LoggedError, match="never rejected"):
            _run(clock, engine, expects_rejection=True)

    def test_an_acceptance_young_at_the_deadline_is_no_rejection(
        self, clock: FakeClock
    ) -> None:
        """A VALID begun just before the deadline still fails the test."""
        engine = _engine(
            clock, lambda now: VALID if now >= SYNC_TIMEOUT - 0.2 else SYNCING
        )
        with pytest.raises(
            LoggedError, match=r"last status: PayloadStatusEnum.VALID\)"
        ):
            _run(clock, engine, expects_rejection=True)


OFF_WIRE = {
    "body": (
        FakePeer(CHAIN, unserved_bodies={2}),
        r"the non-empty body/bodies of block\(s\) 2 never traveled",
    ),
    "header": (
        FakePeer(CHAIN, unserved_headers={1}),
        r"the header\(s\) of block\(s\) 1 never traveled",
    ),
}


class TestWireCoverage:
    """A right verdict passes only when reached over this peer's wire."""

    @pytest.mark.parametrize(
        "verdict,expects_rejection,outcome",
        [
            (VALID, False, "reached the expected head"),
            (INVALID, True, "rejected the invalid chain"),
        ],
        ids=["sync", "rejection"],
    )
    @pytest.mark.parametrize(
        "peer,missing", OFF_WIRE.values(), ids=OFF_WIRE.keys()
    )
    def test_a_verdict_reached_off_wire_fails(
        self,
        clock: FakeClock,
        verdict: PayloadStatusEnum,
        expects_rejection: bool,
        outcome: str,
        peer: FakePeer,
        missing: str,
    ) -> None:
        """A verdict fails on any ancestor header or body not served."""
        with pytest.raises(LoggedError, match=f"{outcome}, but {missing}"):
            _run(
                clock,
                _engine(clock, verdict),
                expects_rejection=expects_rejection,
                imported_at=1.0,
                peer=peer,
            )

    def test_a_header_judgeable_rejection_needs_headers_not_bodies(
        self, clock: FakeClock
    ) -> None:
        """A header-judgeable invalidity owes every header but no body."""
        judgeable = frozenset({BlockException.INCORRECT_EXCESS_BLOB_GAS})
        _run(
            clock,
            _engine(clock, INVALID),
            expects_rejection=True,
            invalidities=judgeable,
            peer=FakePeer(CHAIN, unserved_bodies={1, 2}),
        )
        with pytest.raises(
            LoggedError,
            match=r"rejected the invalid chain, but the header\(s\) of "
            r"block\(s\) 2 never traveled",
        ):
            _run(
                clock,
                _engine(clock, INVALID),
                expects_rejection=True,
                invalidities=judgeable,
                peer=FakePeer(CHAIN, unserved_headers={2}),
            )

    def test_an_unscaffolded_rejection_makes_no_wire_claim(
        self, clock: FakeClock
    ) -> None:
        """A rejection of a chain announcing its own head owes nothing."""
        _run(
            clock,
            _engine(clock, INVALID),
            expects_rejection=True,
            announces_scaffolding=False,
            peer=FakePeer(
                CHAIN, unserved_headers={1, 2}, unserved_bodies={1, 2}
            ),
        )


INVALID_BLOCK_HASH = PayloadStatusEnum.INVALID_BLOCK_HASH


def test_an_invalid_block_hash_answer_fails(clock: FakeClock) -> None:
    """Every served payload hashes to its blockHash, so the answer is wrong."""
    with pytest.raises(LoggedError, match="answered INVALID_BLOCK_HASH"):
        _run(clock, _engine(clock, INVALID_BLOCK_HASH), expects_rejection=True)
    assert clock.now < SYNC_TIMEOUT


class TestLatestValidHash:
    """A rejection that names a latest valid hash must name the right one."""

    def test_the_expected_hash_passes(self, clock: FakeClock) -> None:
        """INVALID naming the first invalid block's parent passes."""
        _run(
            clock,
            _engine(clock, INVALID, latest_valid_hash=Hash(1)),
            expects_rejection=True,
        )

    def test_another_hash_fails(self, clock: FakeClock) -> None:
        """INVALID naming another block blamed the wrong block."""
        with pytest.raises(
            LoggedError,
            match=r"latestValidHash check: mismatch: .* "
            rf"{Hash(2)} \(block 2\), expected {Hash(1)} \(block 1\)",
        ):
            _run(
                clock,
                _engine(clock, INVALID, latest_valid_hash=Hash(2)),
                expects_rejection=True,
            )

    def test_a_hash_off_the_served_chain_fails(self, clock: FakeClock) -> None:
        """A hash the peer never served is named as off the chain."""
        with pytest.raises(
            LoggedError,
            match=rf"{Hash(9)} \(not on the served chain\), expected",
        ):
            _run(
                clock,
                _engine(clock, INVALID, latest_valid_hash=Hash(9)),
                expects_rejection=True,
            )

    @pytest.mark.parametrize(
        "verdict,latest_valid_hash",
        [
            (INVALID, None),
            (INVALID, Hash(0)),
        ],
        ids=["invalid-null", "invalid-zero"],
    )
    def test_no_hash_passes(
        self,
        clock: FakeClock,
        verdict: PayloadStatusEnum,
        latest_valid_hash: Hash | None,
    ) -> None:
        """A rejection naming no latest valid hash is not held against it."""
        _run(
            clock,
            _engine(clock, verdict, latest_valid_hash=latest_valid_hash),
            expects_rejection=True,
            expected_latest_valid_hash=Hash(2),
        )

    def test_a_path_with_no_invalid_block_is_unchecked(
        self, clock: FakeClock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        A hash given for a path that owes none (an error-code-only
        rejection) is logged as unchecked, not failed.
        """
        with caplog.at_level(logging.INFO):
            _run(
                clock,
                _engine(clock, INVALID, latest_valid_hash=Hash(2)),
                expects_rejection=True,
                expected_latest_valid_hash=None,
            )
        assert "latestValidHash check: unchecked" in caplog.text

    def test_a_rejection_without_scaffolding_is_checked(
        self, clock: FakeClock
    ) -> None:
        """
        The check runs even when no wire coverage is asserted, because
        the chain announced its own head.
        """
        with pytest.raises(
            LoggedError, match="latestValidHash check: mismatch"
        ):
            _run(
                clock,
                _engine(clock, INVALID, latest_valid_hash=Hash(2)),
                expects_rejection=True,
                announces_scaffolding=False,
            )


def _path_payload(
    block_hash: int, parent_hash: int, *, invalid: bool = False
) -> FixtureEngineNewPayload:
    """Return a stub payload linking `block_hash` to `parent_hash`."""
    validation_error = BlockException.INVALID_STATE_ROOT if invalid else None
    return cast(
        FixtureEngineNewPayload,
        SimpleNamespace(
            params=[
                SimpleNamespace(
                    block_hash=Hash(block_hash),
                    parent_hash=Hash(parent_hash),
                )
            ],
            validation_error=validation_error,
            valid=lambda: validation_error is None,
        ),
    )


class TestExpectedLatestValidHash:
    """The owed hash is the parent of the first invalid block served."""

    def test_a_scaffolded_path_owes_the_parent_of_its_first_invalid_block(
        self,
    ) -> None:
        """The sync target and the blocks above the invalid one are moot."""
        path = SyncPath(
            index=0,
            total=1,
            target=_path_payload(5, 4),
            authored=(
                _path_payload(1, 0),
                _path_payload(2, 1),
                _path_payload(3, 2, invalid=True),
                _path_payload(4, 3, invalid=True),
            ),
            announces_scaffolding=True,
        )
        assert path.expected_latest_valid_hash == Hash(2)

    def test_each_target_owes_the_parent_on_its_own_path(self) -> None:
        """Siblings sharing a trunk each owe their own invalid block's."""
        trunk = (_path_payload(1, 0), _path_payload(2, 1))
        invalid_leaf = _path_payload(3, 2, invalid=True)
        invalid_branch = (_path_payload(4, 1, invalid=True),)
        valid_leaf = _path_payload(5, 2)
        first, second, third = (
            SyncPath(
                index=index,
                total=3,
                target=_path_payload(10 + index, leaf),
                authored=authored,
                announces_scaffolding=True,
            )
            for index, (leaf, authored) in enumerate(
                [
                    (3, (*trunk, invalid_leaf)),
                    (4, (trunk[0], *invalid_branch)),
                    (5, (*trunk, valid_leaf)),
                ]
            )
        )
        assert first.expected_latest_valid_hash == Hash(2)
        assert second.expected_latest_valid_hash == Hash(1)
        assert third.expected_latest_valid_hash is None

    def test_an_invalid_first_block_owes_genesis(self) -> None:
        """A path invalid from its first block owes the genesis hash."""
        path = SyncPath(
            index=0,
            total=1,
            target=_path_payload(2, 1),
            authored=(_path_payload(1, 0, invalid=True),),
            announces_scaffolding=True,
        )
        assert path.expected_latest_valid_hash == GENESIS_HASH


class RefusingPeer(FakePeer):
    """
    A dropped peer whose first `refusals` redials raise `error`.

    `redial_times` records the fake time of every redial.
    """

    def __init__(
        self, clock: FakeClock, refusals: int, error: Exception
    ) -> None:
        """Start dropped."""
        super().__init__(CHAIN, alive=False)
        self.clock = clock
        self.refusals = refusals
        self.error = error
        self.redial_times: list[float] = []

    def reconnect(self, chain: Chain, timeout: float = 30.0) -> None:
        """Refuse the first redials, then reconnect."""
        del chain, timeout
        self.redial_times.append(self.clock.now)
        if len(self.redial_times) <= self.refusals:
            raise self.error
        self.alive = True


REDIAL_REFUSALS = {
    "connection-refused": ConnectionRefusedError("client refused"),
    "handshake-timeout": TimeoutError("no Hello"),
    "disconnect-on-hello": RLPxError("client refused the connection: 5"),
}


@pytest.mark.parametrize(
    "error", REDIAL_REFUSALS.values(), ids=REDIAL_REFUSALS.keys()
)
@pytest.mark.parametrize(
    "verdict,expects_rejection",
    [(VALID, False), (INVALID, True)],
    ids=["sync", "rejection"],
)
def test_a_refused_redial_is_retried_at_the_next_announcement(
    clock: FakeClock,
    verdict: PayloadStatusEnum,
    expects_rejection: bool,
    error: Exception,
) -> None:
    """
    A redial the client refuses does not end the test: it is retried at
    each later announcement, never sooner, until one succeeds.
    """
    peer = RefusingPeer(clock, refusals=2, error=error)
    _run(
        clock,
        _engine(clock, lambda now: verdict if now >= 10.0 else SYNCING),
        expects_rejection=expects_rejection,
        imported_at=10.0,
        peer=peer,
    )
    assert len(peer.redial_times) == 3
    assert all(
        later - earlier >= ANNOUNCE_INTERVAL - 1e-9
        for earlier, later in pairwise(peer.redial_times)
    )


def test_the_redial_warning_names_the_disconnect_reason(
    clock: FakeClock, caplog: pytest.LogCaptureFixture
) -> None:
    """The reason the client gave for the drop is logged with the redial."""
    peer = FakePeer(CHAIN, alive=False, disconnect_reason=4)
    with caplog.at_level(logging.WARNING):
        _run(
            clock,
            _engine(clock, lambda now: VALID if now >= 10.0 else SYNCING),
            imported_at=10.0,
            peer=peer,
        )
    assert peer.redials == 1
    assert "Peer dropped mid-sync (Disconnect reason 4); redialing" in (
        caplog.text
    )


class _LandingAt(set[Hash]):
    """Served hashes whose record lands only at a fake time."""

    def __init__(self, clock: FakeClock, lands_at: float, hashes: Any) -> None:
        """Hold `hashes`, readable from `lands_at` on."""
        super().__init__(hashes)
        self.clock = clock
        self.lands_at = lands_at

    def __contains__(self, item: object) -> bool:
        """Report a hash as served only once its record has landed."""
        return self.clock.now >= self.lands_at and super().__contains__(item)


def test_evidence_landing_late_within_the_grace_still_counts(
    clock: FakeClock,
) -> None:
    """
    A held-back peer thread records the bodies after the verdict but
    within the grace, which the check waits out by re-reading.
    """
    peer = FakePeer(CHAIN)
    lands_at = 0.3
    peer.body_hashes_ever_served = _LandingAt(
        clock, lands_at, peer.body_hashes_ever_served
    )
    test_via_wirex.assert_wire_coverage(
        CHAIN, cast(MockPeer, peer), "reached the expected head"
    )
    assert lands_at <= clock.now < lands_at + 0.1


def test_evidence_that_never_lands_fails_after_the_grace(
    clock: FakeClock,
) -> None:
    """A body never served fails once the grace has passed, not sooner."""
    with pytest.raises(LoggedError, match=r"block\(s\) 2 never traveled"):
        test_via_wirex.assert_wire_coverage(
            CHAIN,
            cast(MockPeer, FakePeer(CHAIN, unserved_bodies={2})),
            "reached the expected head",
        )
    assert clock.now >= test_via_wirex.EVIDENCE_GRACE_TIME


CONFIRMATION_FAILURES = {
    "non-valid-confirmation": (
        {"confirmation": SYNCING},
        {},
        "failed to sync to .*SYNCING",
    ),
    "confirmation-timeout": (
        {
            "confirmation": ForkchoiceUpdateTimeoutError(
                attempts=10,
                elapsed=5.0,
                interval=0.5,
                final_status=SYNCING,
            )
        },
        {},
        "never made it canonical",
    ),
    "wrong-latest-head": (
        {},
        {"latest": {"hash": str(Hash(2))}},
        f"Client head is {Hash(2)}",
    ),
    "missing-latest-head": ({}, {"latest": None}, "returned no head block"),
}


@pytest.mark.parametrize(
    "engine_knobs,overrides,match",
    CONFIRMATION_FAILURES.values(),
    ids=CONFIRMATION_FAILURES.keys(),
)
def test_an_imported_head_must_be_confirmed_and_latest(
    clock: FakeClock,
    engine_knobs: dict[str, Any],
    overrides: dict[int | str, Any],
    match: str,
) -> None:
    """An imported head fails unless made canonical and reported latest."""
    with pytest.raises(LoggedError, match=match):
        _run(
            clock,
            _engine(clock, **engine_knobs),
            imported_at=1.0,
            overrides=overrides,
        )


def _genesis(state_root: int) -> FixtureHeader:
    """Return a genesis header told apart by its `state_root`."""
    return FixtureHeader(
        fee_recipient=Address(0),
        state_root=Hash(state_root),
        number=0,
        gas_limit=30_000_000,
        timestamp=0,
        extra_data=Bytes(b""),
    )


def _rpc_block(header: FixtureHeader) -> dict[str, Any]:
    """Return `header` as `eth_getBlockByNumber` answers it."""
    return header.model_dump(mode="json", by_alias=True)


class TestGenesisVerification:
    """A client is run only on the group's genesis."""

    def test_a_matching_genesis_passes(self, clock: FakeClock) -> None:
        """A client whose genesis is the group's syncs as usual."""
        genesis = _genesis(1)
        _run(
            clock,
            _engine(clock),
            imported_at=1.0,
            overrides={0: _rpc_block(genesis)},
            genesis_header=genesis,
        )

    def test_a_mismatched_genesis_fails(self, clock: FakeClock) -> None:
        """A client on another genesis fails before anything is announced."""
        engine = _engine(clock)
        with pytest.raises(
            GenesisBlockMismatchExceptionError, match="hash mismatch"
        ):
            _run(
                clock,
                engine,
                imported_at=1.0,
                overrides={0: _rpc_block(_genesis(2))},
                genesis_header=_genesis(1),
            )
        assert engine.forkchoice_calls == 0

    def test_a_missing_genesis_fails(self, clock: FakeClock) -> None:
        """A client that returns no genesis block fails."""
        with pytest.raises(LoggedError, match="returned no genesis block"):
            _run(
                clock,
                _engine(clock),
                imported_at=1.0,
                overrides={0: None},
                genesis_header=_genesis(1),
            )


REFUSAL_CODE = -32602


@dataclass(frozen=True)
class RefusalSite:
    """Where in the loop the client refuses the head, and when."""

    expects_rejection: bool
    knobs: dict[str, Any]
    refused_at: tuple[float, float]


REFUSAL_SITES = {
    "valid-announcement": RefusalSite(
        False, {"refusal": lambda _now: REFUSAL_CODE}, (0.0, 0.0)
    ),
    "rejection-announcement": RefusalSite(
        True, {"refusal": lambda _now: REFUSAL_CODE}, (0.0, 0.0)
    ),
    "rejection-poll": RefusalSite(
        True,
        {"refusal": lambda now: REFUSAL_CODE if now >= 1.0 else None},
        (1.0, 1.01),
    ),
    "rejection-reannouncement": RefusalSite(
        True,
        {"forkchoice_refusal": lambda call: REFUSAL_CODE if call else None},
        (ANNOUNCE_INTERVAL, ANNOUNCE_INTERVAL + 0.01),
    ),
}


@pytest.mark.parametrize(
    "site", REFUSAL_SITES.values(), ids=REFUSAL_SITES.keys()
)
class TestRpcRefusal:
    """An Engine API error is a verdict only with the declared code."""

    @staticmethod
    def _run_refused(
        clock: FakeClock, site: RefusalSite, declared: int | None
    ) -> None:
        """Run a case declaring `declared` against a refusing client."""
        _run(
            clock,
            _engine(clock, **site.knobs),
            expects_rejection=site.expects_rejection,
            error_code=declared,
        )

    def test_the_declared_code_passes(
        self, clock: FakeClock, site: RefusalSite
    ) -> None:
        """A refusal with the declared code ends the test, passing."""
        self._run_refused(clock, site, REFUSAL_CODE)
        earliest, latest = site.refused_at
        assert earliest <= clock.now <= latest

    def test_a_wrong_code_fails(
        self, clock: FakeClock, site: RefusalSite
    ) -> None:
        """A refusal with another code than the declared one fails."""
        with pytest.raises(LoggedError, match="wrong error code"):
            self._run_refused(clock, site, -38003)

    def test_an_undeclared_refusal_is_raised(
        self, clock: FakeClock, site: RefusalSite
    ) -> None:
        """A refusal the fixture does not declare propagates."""
        with pytest.raises(JSONRPCError):
            self._run_refused(clock, site, None)


def test_every_target_of_a_fixture_runs_and_is_judged(
    clock: FakeClock,
) -> None:
    """A later target that never syncs fails, named by its position."""
    second_chain = _chain(4)
    first = _case(CHAIN, expects_rejection=False, total=2)
    second = _case(second_chain, expects_rejection=False, index=1, total=2)
    entered = []

    @contextmanager
    def target_context(case: SyncTargetCase) -> Iterator[Any]:
        """Hand `case` a client that never imports its head."""
        entered.append(case)
        yield SimpleNamespace(
            client=SimpleNamespace(id="client"),
            eth_rpc=FakeEth(clock, _head(second_chain), NEVER),
            engine_rpc=_engine(clock),
            mock_peer=FakePeer(second_chain),
        )

    with pytest.raises(LoggedError, match="^target 1: Client never imported"):
        test_via_wirex.test_blockchain_via_wirex(
            timing_data=TimingData("Total"),
            eth_rpc=cast(EthRPC, FakeEth(clock, _head(CHAIN), 1.0)),
            engine_rpc=cast(EngineRPC, _engine(clock)),
            client=cast(Any, SimpleNamespace(id="client")),
            genesis_verified_clients={"client"},
            genesis_header=cast(FixtureHeader, _StubHeader(0, GENESIS_HASH)),
            sync_target_cases=[first, second],
            mock_peer=cast(MockPeer, FakePeer(CHAIN)),
            target_context_factory=target_context,
            wirex_sync_timeout=SYNC_TIMEOUT,
            wirex_poll_interval=POLL_INTERVAL,
            wirex_announce_interval=ANNOUNCE_INTERVAL,
        )
    assert entered == [second]
