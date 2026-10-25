"""
Tests for the wirex test body's wait loops.

The Engine API and devp2p sides are replaced by small fakes and the
module's clock by a fake one, so a client that blocks an announcement
for minutes, or drops the peer mid-sync, is simulated in microseconds.
"""

import inspect
import logging
from contextlib import AbstractContextManager, contextmanager, nullcontext
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


def _chain(length: int, genesis_hash: int = 0) -> Chain:
    """Return a chain of `length` non-empty blocks above a stub genesis."""
    genesis = _StubHeader(number=0, block_hash=Hash(genesis_hash))
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
    served_payloads = [
        SimpleNamespace(
            params=[SimpleNamespace(block_hash=block.block_hash)],
            new_payload_version=4,
        )
        for block in chain.blocks
    ]
    path = SimpleNamespace(
        target=target,
        served_payloads=served_payloads,
        expects_rejection=expects_rejection,
        announces_scaffolding=announces_scaffolding,
        checks_wire_coverage=not expects_rejection or announces_scaffolding,
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
    long the n-th `forkchoiceUpdated` of an announcement blocks,
    `forkchoice_verdict` its status and `forkchoice_refusal` the error
    code it raises; `confirmation` is the answer, or the exception, of
    the confirming update.
    `latest_valid_hash` comes with every `newPayload` answer.

    A `newPayload` for a block other than `head`, the hash of `CHAIN`'s
    head, is the confirmation of a block below it: `below_head_verdict`
    answers it, and `below_head_calls` records its hash.
    """

    clock: FakeClock
    verdict: Callable[[float], PayloadStatusEnum]
    forkchoice_delay: Callable[[int], float] = lambda _call: 0.0
    forkchoice_verdict: Callable[[int], PayloadStatusEnum] = (
        lambda _call: PayloadStatusEnum.SYNCING
    )
    refusal: Callable[[float], int | None] = lambda _now: None
    forkchoice_refusal: Callable[[int], int | None] = lambda _call: None
    confirmation: PayloadStatusEnum | Exception = PayloadStatusEnum.VALID
    latest_valid_hash: Hash | None = None
    forkchoice_calls: int = 0
    head: Hash = Hash(3)
    below_head_verdict: Callable[[float], PayloadStatusEnum] = (
        lambda _now: PayloadStatusEnum.VALID
    )
    below_head_calls: list[Hash] = field(default_factory=list)

    def new_payload(self, *params: Any, version: int) -> PayloadStatus:
        """Answer with the verdict of this instant, or refuse."""
        del version
        block_hash = params[0].block_hash
        if block_hash != self.head:
            self.below_head_calls.append(block_hash)
            return _status(self.below_head_verdict(self.clock.now))
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
        return _response(self.forkchoice_verdict(call))

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


ACCEPTANCE_SITES = {
    "first-announcement": ({"verdict": VALID}, 0.0, "engine_newPayload"),
    "turning-invalid-later": (
        {"verdict": lambda now: VALID if now < 0.3 else INVALID},
        0.0,
        "engine_newPayload",
    ),
    "later-poll": (
        {"verdict": lambda now: VALID if now >= 1.0 else SYNCING},
        1.0,
        "engine_newPayload",
    ),
    "first-forkchoice-reply": (
        {"forkchoice_verdict": lambda _call: VALID},
        0.0,
        "engine_forkchoiceUpdated",
    ),
    "reannouncement-forkchoice-reply": (
        {"forkchoice_verdict": lambda call: VALID if call else SYNCING},
        ANNOUNCE_INTERVAL,
        "engine_forkchoiceUpdated",
    ),
}


@pytest.mark.parametrize(
    "knobs,accepted_at,method",
    ACCEPTANCE_SITES.values(),
    ids=ACCEPTANCE_SITES.keys(),
)
def test_any_acceptance_of_an_invalid_head_fails_at_once(
    clock: FakeClock,
    knobs: dict[str, Any],
    accepted_at: float,
    method: str,
) -> None:
    """A VALID from either method, at any point, fails there and then."""
    with pytest.raises(
        LoggedError,
        match=f"accepted the invalid chain: {method} answered VALID",
    ):
        _run(clock, _engine(clock, **knobs), expects_rejection=True)
    assert accepted_at <= clock.now < accepted_at + 0.01


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


LATEST_VALID_HASH_ANSWERS = {
    # INVALID naming the first invalid block's parent passes.
    "expected-hash": (Hash(1), Hash(1), "match"),
    # INVALID naming another block blamed the wrong block.
    "another-hash": (
        Hash(2),
        Hash(1),
        rf"mismatch: .* {Hash(2)} \(block 2\), expected {Hash(1)} \(block 1\)",
    ),
    "off-the-served-chain": (
        Hash(9),
        Hash(1),
        rf"mismatch: .* {Hash(9)} \(not on the served chain\), expected",
    ),
    # A rejection naming no latest valid hash is not held against it.
    "null": (None, Hash(2), "null"),
    # The all-zero hash names a PoW ancestor, which is only genesis.
    "zero-for-genesis": (Hash(0), Hash(100), "match"),
    "zero-for-a-block": (Hash(0), Hash(2), "mismatch"),
    # A path that owes none, rejected by an error code only, is unchecked.
    "no-invalid-block": (Hash(2), None, "unchecked"),
}
"""The hash given, the hash owed, and the check's result for them."""


class TestLatestValidHash:
    """A rejection that names a latest valid hash must name the right one."""

    @pytest.mark.parametrize(
        "given,owed,result",
        LATEST_VALID_HASH_ANSWERS.values(),
        ids=LATEST_VALID_HASH_ANSWERS.keys(),
    )
    def test_the_hash_is_checked_against_the_owed_one(
        self,
        caplog: pytest.LogCaptureFixture,
        given: Hash | None,
        owed: Hash | None,
        result: str,
    ) -> None:
        """A mismatch fails the test, and every other result is logged."""
        path = cast(SyncPath, SimpleNamespace(expected_latest_valid_hash=owed))
        chain = _chain(3, genesis_hash=100)

        def check() -> None:
            test_via_wirex.check_latest_valid_hash(
                path, chain, _status(INVALID, given), ""
            )

        if result.startswith("mismatch"):
            with pytest.raises(
                LoggedError, match=f"latestValidHash check: {result}"
            ):
                check()
        else:
            with caplog.at_level(logging.INFO):
                check()
            assert f"latestValidHash check: {result}" in caplog.text

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


def _refuse_the_parent(_now: float) -> PayloadStatusEnum:
    """Refuse the confirmation at the RPC layer, as erigon can."""
    raise JSONRPCError(-32000, "append with gap blockNum=2")


LATEST_VALID_BLOCK_ANSWERS = {
    # A client still fetching the block may answer SYNCING first.
    "valid-after-a-wait": (
        lambda now: VALID if now >= 2.0 else SYNCING,
        FIRST_INVALID_PARENT,
        None,
        (2.0, 2.01),
    ),
    # A client rejecting the valid parent too blamed a valid block.
    "rejected": (
        lambda _now: INVALID,
        FIRST_INVALID_PARENT,
        rf"answered PayloadStatusEnum.INVALID for {Hash(1)}",
        (0.0, 0.01),
    ),
    "never-confirmed": (
        lambda _now: SYNCING,
        FIRST_INVALID_PARENT,
        f"never confirmed {Hash(1)}",
        (SYNC_TIMEOUT, SYNC_TIMEOUT + 1),
    ),
    # An RPC refusal of the valid parent is a verdict, not a traceback.
    "refused-at-the-rpc-layer": (
        _refuse_the_parent,
        FIRST_INVALID_PARENT,
        rf"refused {Hash(1)}, the valid parent .* at the RPC layer",
        (0.0, 0.01),
    ),
    # Genesis is no payload, so nothing is sent for it.
    "genesis-parent": (lambda _now: INVALID, GENESIS_HASH, None, (0.0, 0.01)),
}
"""
How the client answers for the block below the head, the hash owed,
the failure expected, if any, and when the test ends.
"""


@pytest.mark.parametrize(
    "verdict,owed,failure,ends",
    LATEST_VALID_BLOCK_ANSWERS.values(),
    ids=LATEST_VALID_BLOCK_ANSWERS.keys(),
)
def test_the_latest_valid_block_must_be_valid(
    clock: FakeClock,
    verdict: Callable[[float], PayloadStatusEnum],
    owed: Hash,
    failure: str | None,
    ends: tuple[float, float],
) -> None:
    """After a rejection, the block owed as latest valid must be VALID."""
    engine = _engine(clock, INVALID, below_head_verdict=verdict)
    outcome: AbstractContextManager[Any] = (
        nullcontext()
        if failure is None
        else pytest.raises(LoggedError, match=failure)
    )
    with outcome:
        _run(
            clock,
            engine,
            expects_rejection=True,
            expected_latest_valid_hash=owed,
        )
    assert set(engine.below_head_calls) == {owed} - {GENESIS_HASH}
    earliest, latest = ends
    assert earliest <= clock.now < latest


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


OWED_HASHES = {
    # The sync target and the blocks above the invalid one are moot.
    "two-invalid-blocks": (
        [(1, 0, False), (2, 1, False), (3, 2, True), (4, 3, True)],
        2,
    ),
    # Siblings sharing a trunk each owe their own invalid block's parent.
    "invalid-leaf-on-the-trunk": (
        [(1, 0, False), (2, 1, False), (3, 2, True)],
        2,
    ),
    "invalid-branch-off-the-trunk": ([(1, 0, False), (4, 1, True)], 1),
    "valid-leaf": ([(1, 0, False), (2, 1, False), (5, 2, False)], None),
    "invalid-first-block": ([(1, 0, True)], 0),
}
"""A path's authored blocks (hash, parent, invalid) and the hash owed."""


@pytest.mark.parametrize(
    "authored,owed", OWED_HASHES.values(), ids=OWED_HASHES.keys()
)
def test_a_path_owes_the_parent_of_its_first_invalid_block(
    authored: list[tuple[int, int, bool]], owed: int | None
) -> None:
    """The owed hash is the parent of the first invalid block served."""
    path = SyncPath(
        index=0,
        total=1,
        target=_path_payload(10, authored[-1][0]),
        authored=tuple(
            _path_payload(block, parent, invalid=invalid)
            for block, parent, invalid in authored
        ),
        announces_scaffolding=True,
    )
    assert path.expected_latest_valid_hash == (
        None if owed is None else Hash(owed)
    )


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


GENESIS_ANSWERS = {
    "matching": (_rpc_block(_genesis(1)), None),
    "mismatched": (
        _rpc_block(_genesis(2)),
        (GenesisBlockMismatchExceptionError, "hash mismatch"),
    ),
    "missing": (None, (LoggedError, "returned no genesis block")),
}
"""The genesis block the client answers, and the failure it causes."""


@pytest.mark.parametrize(
    "answer,failure", GENESIS_ANSWERS.values(), ids=GENESIS_ANSWERS.keys()
)
def test_a_client_runs_only_on_the_groups_genesis(
    clock: FakeClock,
    answer: dict[str, Any] | None,
    failure: tuple[type[Exception], str] | None,
) -> None:
    """A client on another genesis, or none, fails before any announcement."""
    engine = _engine(clock)
    outcome: AbstractContextManager[Any] = (
        nullcontext()
        if failure is None
        else pytest.raises(failure[0], match=failure[1])
    )
    with outcome:
        _run(
            clock,
            engine,
            imported_at=1.0,
            overrides={0: answer},
            genesis_header=_genesis(1),
        )
    assert (engine.forkchoice_calls == 0) == (failure is not None)


REFUSAL_CODE = -32602


REFUSED_ALWAYS = {"refusal": lambda _now: REFUSAL_CODE}
"""A client refusing every `newPayload` with `REFUSAL_CODE`."""

REFUSALS = {
    # A refusal with the declared code ends the test at once, passing.
    "declared-valid-path": (False, REFUSED_ALWAYS, REFUSAL_CODE, None),
    "declared-rejection-path": (True, REFUSED_ALWAYS, REFUSAL_CODE, None),
    # A refusal with another code than the declared one fails.
    "wrong-code-valid-path": (
        False,
        REFUSED_ALWAYS,
        -38003,
        (LoggedError, "wrong error code"),
    ),
    "wrong-code-rejection-path": (
        True,
        REFUSED_ALWAYS,
        -38003,
        (LoggedError, "wrong error code"),
    ),
    # A refusal the fixture does not declare propagates.
    "undeclared-valid-path": (
        False,
        REFUSED_ALWAYS,
        None,
        (JSONRPCError, None),
    ),
    "undeclared-rejection-path": (
        True,
        REFUSED_ALWAYS,
        None,
        (JSONRPCError, None),
    ),
    # Any newPayload answer fails a head declaring an error code, so
    # does a refusal that comes late or from forkchoiceUpdated.
    **{
        name: (
            True,
            knobs,
            REFUSAL_CODE,
            (LoggedError, "instead of refusing the head"),
        )
        for name, knobs in {
            "invalid-status": {"verdict": INVALID},
            "valid-status": {"verdict": VALID},
            "refused-after-syncing": {
                "refusal": lambda now: REFUSAL_CODE if now >= 1.0 else None
            },
            "refused-by-forkchoice": {
                "forkchoice_refusal": lambda _call: REFUSAL_CODE
            },
        }.items()
    },
}
"""Whether the path is a rejection, the client, the code declared, and
the failure expected, if any."""


@pytest.mark.parametrize(
    "expects_rejection,knobs,declared,failure",
    REFUSALS.values(),
    ids=REFUSALS.keys(),
)
def test_an_rpc_refusal_is_a_verdict_only_with_the_declared_code(
    clock: FakeClock,
    expects_rejection: bool,
    knobs: dict[str, Any],
    declared: int | None,
    failure: tuple[type[Exception], str | None] | None,
) -> None:
    """Only `newPayload` refusing with the declared code passes, at once."""
    outcome: AbstractContextManager[Any] = (
        nullcontext()
        if failure is None
        else pytest.raises(failure[0], match=failure[1])
    )
    with outcome:
        _run(
            clock,
            _engine(clock, **knobs),
            expects_rejection=expects_rejection,
            error_code=declared,
        )
    assert clock.now == 0.0


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
