"""
Tests for the wirex simulator's wire-coverage and client contracts.

Path resolution and its classification live in
`test_wirex_sync_targets`; this module covers what happens above a
resolved chain: which headers and bodies the per-hash coverage check
demands, and when a test reuses, replaces or isolates its client.
"""

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, cast

import pytest

from execution_testing.base_types import Address, Bytes, Hash
from execution_testing.devp2p.chain import Block, Chain
from execution_testing.devp2p.peer import MockPeer, PeerStatistics
from execution_testing.devp2p.protocol import ForkSchedule
from execution_testing.devp2p.rlpx import RLPxError
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import (
    ALL_FORKS_WITH_TRANSITIONS,
    Cancun,
    Paris,
    ParisToShanghaiAtTime15k,
)
from execution_testing.test_types.block_types import Withdrawal

from ..simulators.helpers.exceptions import LoggedError
from ..simulators.helpers.ruleset import ruleset
from ..simulators.helpers.timing import TimingData
from ..simulators.simulator_logic import test_via_wirex
from ..simulators.simulator_logic.test_via_wirex import (
    assert_wire_coverage,
    required_wire_bodies,
    required_wire_headers,
)
from ..simulators.wirex import client_policy
from ..simulators.wirex import conftest as wirex
from ..simulators.wirex.client_policy import (
    HEAD_LOOKUP_TIMEOUT,
    MAX_REORG_DEPTH,
    ClientHead,
    reorg_depth,
    replacement_reason,
)
from .direct_calls import fixture_body


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


def _peer(chain: Chain, *, bodies: set[int]) -> MockPeer:
    """Return a peer that served every header and the `bodies` named."""
    return cast(
        MockPeer,
        SimpleNamespace(
            header_hashes_ever_served={b.block_hash for b in chain.blocks},
            body_hashes_ever_served={
                b.block_hash for b in chain.blocks if b.number in bodies
            },
            statistics=PeerStatistics(),
        ),
    )


class TestRequiredWireBodies:
    """Which bodies the wire-coverage check demands, per chain shape."""

    def test_the_announced_head_is_exempt(self) -> None:
        """A non-empty head body is never owed, so a peer may skip it."""
        ancestors = [_block(1, empty=False), _block(2, empty=False)]
        chain = _chain([*ancestors, _block(3, empty=False)])
        assert required_wire_bodies(chain) == ancestors
        assert_wire_coverage(chain, _peer(chain, bodies={1, 2}), "synced")

    def test_a_missing_ancestor_is_named(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An ancestor body that never traveled fails, by number."""
        now = [0.0]

        def sleep(seconds: float) -> None:
            """Let the evidence grace pass at once."""
            now[0] += seconds

        monkeypatch.setattr(
            test_via_wirex,
            "time",
            SimpleNamespace(sleep=sleep, monotonic=lambda: now[0]),
        )
        chain = _chain(
            [
                _block(1, empty=False),
                _block(2, empty=False),
                _block(3, empty=True),
            ]
        )
        with pytest.raises(
            LoggedError,
            match=r"The client synced, but the non-empty body/bodies of "
            r"block\(s\) 2 never traveled",
        ):
            assert_wire_coverage(chain, _peer(chain, bodies={1}), "synced")

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
        """The invalid block below a rejection target owes its body."""
        chain = _chain([_block(1, empty=False), _block(2, empty=True)])
        assert [b.number for b in required_wire_bodies(chain)] == [1]

    def test_a_withdrawals_only_body_is_owed(self) -> None:
        """Withdrawals alone make a body its header cannot stand for."""
        withdrawal = Withdrawal(
            index=0, validator_index=0, address=Address(1), amount=1
        )
        withdrawals_only = Block(
            header=cast(FixtureHeader, _StubHeader(1, Hash(1))),
            transactions=[],
            withdrawals=[withdrawal],
        )
        chain = _chain([withdrawals_only, _block(2, empty=True)])
        assert required_wire_bodies(chain) == [withdrawals_only]


class TestRequiredWireHeaders:
    """Which headers the wire-coverage check demands."""

    def test_every_block_below_the_head_is_owed(self) -> None:
        """Every header but the head's is owed, empty body or not."""
        blocks = [
            _block(1, empty=True),
            _block(2, empty=False),
            _block(3, empty=True),
        ]
        assert required_wire_headers(_chain(blocks)) == blocks[:-1]


def _fork(length: int, *, branch: int, shared: int = 0) -> Chain:
    """
    Return a chain of `length` blocks whose first `shared` blocks are
    the trunk every branch shares, and whose rest is `branch`'s own.
    """
    blocks = []
    for number in range(1, length + 1):
        owner = 0 if number <= shared else branch
        header = _StubHeader(
            number=number, block_hash=Hash(owner * 100_000 + number)
        )
        blocks.append(
            Block(
                header=cast(FixtureHeader, header),
                transactions=[Bytes(b"\x01")],
                withdrawals=None,
            )
        )
    return _chain(blocks)


class TestReorgDepth:
    """How far below its head a reused client must unwind."""

    def test_a_chain_forking_at_genesis_unwinds_the_whole_head(self) -> None:
        """Sibling chains share only genesis."""
        old, new = _fork(259, branch=1), _fork(268, branch=2)
        assert reorg_depth(259, old, new) == 259

    def test_a_shared_trunk_is_not_unwound(self) -> None:
        """A chain extending the head's ancestry unwinds only above it."""
        old = _fork(259, branch=1, shared=200)
        new = _fork(268, branch=2, shared=200)
        assert reorg_depth(259, old, new) == 59

    def test_an_extension_needs_no_reorg(self) -> None:
        """A chain continuing the head's own chain unwinds nothing."""
        assert reorg_depth(3, _fork(3, branch=1), _fork(259, branch=1)) == 0

    def test_a_head_on_no_served_chain_shares_only_genesis(self) -> None:
        """Without the head's ancestry, the fork is taken at genesis."""
        assert reorg_depth(69, None, _fork(258, branch=2)) == 69


class _FakeManager:
    """The manager calls the client fixture makes, recorded in order."""

    def __init__(self, running: Any) -> None:
        """Hold the group's `running` client, or `None`."""
        self.running = running
        self.calls: list[tuple[str, ...]] = []

    def get_client(self, identifier: str) -> Any:
        """Record the lookup and return the running client."""
        self.calls.append(("get", identifier))
        return self.running

    def discard_client(self, identifier: str) -> None:
        """Record the discard."""
        self.calls.append(("discard", identifier))

    def mark_test_completed(self, identifier: str, nodeid: str) -> None:
        """Record the completion."""
        self.calls.append(("completed", identifier, nodeid))


GROUP = "0xdeadbeef-go-ethereum"


class TestClientFixture:
    """The client fixture acts on the reuse decision."""

    @pytest.fixture
    def booted(self, monkeypatch: pytest.MonkeyPatch) -> list[str]:
        """Stand in for client boots, recording each identifier booted."""
        booted: list[str] = []

        def boot(*args: Any) -> Any:
            identifier = args[2]
            booted.append(identifier)
            return SimpleNamespace(id=identifier)

        def group_client(*_args: Any) -> Any:
            booted.append(GROUP)
            yield SimpleNamespace(id=GROUP)

        monkeypatch.setattr(
            client_policy, "group_identifier_of", lambda _node: GROUP
        )
        monkeypatch.setattr(client_policy, "boot_managed_client", boot)
        monkeypatch.setattr(client_policy, "group_client", group_client)
        return booted

    @staticmethod
    def _run(manager: _FakeManager, cases: list[Any]) -> Any:
        """Run the fixture through its teardown and return its client."""
        generator = fixture_body(client_policy.client)(
            multi_test_hive_test=None,
            multi_test_client_manager=manager,
            client_type=None,
            environment={},
            client_genesis={},
            total_timing_data=None,
            request=SimpleNamespace(node=SimpleNamespace(nodeid="test[x]")),
            sync_target_cases=cases,
            mock_peers={},
        )
        client = next(generator)
        with pytest.raises(StopIteration):
            next(generator)
        return client

    @pytest.mark.parametrize(
        "reason,discarded",
        [("a deep reorg", True), (None, False)],
        ids=["reason", "no-reason"],
    )
    def test_a_reason_replaces_the_group_client(
        self,
        monkeypatch: pytest.MonkeyPatch,
        booted: list[str],
        reason: str | None,
        discarded: bool,
    ) -> None:
        """A reason discards the running client, and no reason keeps it."""
        monkeypatch.setattr(
            client_policy, "replacement_reason", lambda *_args: reason
        )
        manager = _FakeManager(running=SimpleNamespace(id="running"))
        self._run(manager, [SimpleNamespace()])
        assert (("discard", GROUP) in manager.calls) == discarded
        assert booted == [GROUP]

    def test_a_first_test_has_nothing_to_replace(
        self, monkeypatch: pytest.MonkeyPatch, booted: list[str]
    ) -> None:
        """Without a running client, no reason is asked for."""

        def reason(*_args: Any) -> str | None:
            raise AssertionError("there is no client to judge")

        monkeypatch.setattr(client_policy, "replacement_reason", reason)
        manager = _FakeManager(running=None)
        self._run(manager, [SimpleNamespace()])
        assert manager.calls == [("get", GROUP)]
        assert booted == [GROUP]

    def test_a_multi_target_fixture_runs_on_an_isolated_client(
        self, booted: list[str]
    ) -> None:
        """
        The first target boots its own client, discarded at teardown,
        and the test still counts toward its group's completion.
        """
        cases = [
            SimpleNamespace(
                path=SimpleNamespace(index=index, total=2, name=f"t{index}")
            )
            for index in range(2)
        ]
        manager = _FakeManager(running=SimpleNamespace(id="running"))
        client = self._run(manager, cases)
        assert client.id == booted[0] == f"{GROUP}-t0"
        assert manager.calls == [
            ("discard", f"{GROUP}-t0"),
            ("completed", GROUP, "test[x]"),
        ]


class TestReplacementReason:
    """When a single-target fixture must not reuse the group client."""

    def _reason(
        self,
        monkeypatch: pytest.MonkeyPatch,
        head: Chain,
        chain: Chain,
        *,
        expects_rejection: bool = False,
        engine_only: frozenset[int] = frozenset(),
    ) -> str | None:
        """
        Return the verdict for `chain` on a client at `head`'s top.

        The peer served `head`'s headers, bar the blocks numbered in
        `engine_only`, which reached the client over the Engine API.
        """
        monkeypatch.setattr(
            client_policy,
            "client_head",
            lambda _client: ClientHead(head.head.number, head.head.block_hash),
        )
        peer = SimpleNamespace(
            served_chain_holding=lambda block_hash: (
                head if head.number_of(block_hash) is not None else None
            ),
            header_hashes_ever_served={
                block.block_hash
                for block in head.blocks
                if block.number not in engine_only
            },
        )
        case = SimpleNamespace(
            chain=chain,
            path=SimpleNamespace(expects_rejection=expects_rejection),
        )
        return replacement_reason(
            cast(Any, SimpleNamespace(id="c")),
            cast(Any, case),
            cast(Any, peer),
        )

    def test_a_shallow_reorg_reuses_the_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A sibling chain at the depth limit runs on the reused client."""
        head = _fork(MAX_REORG_DEPTH, branch=1)
        assert self._reason(monkeypatch, head, _fork(70, branch=2)) is None

    def test_a_deep_reorg_replaces_the_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A sibling chain forking at genesis below a 259-block head."""
        reason = self._reason(
            monkeypatch, _fork(259, branch=1), _fork(268, branch=2)
        )
        assert reason is not None and "259 blocks" in reason

    def test_an_engine_only_ancestor_replaces_the_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        A chain extending a head the client got over the Engine API
        alone needs that head as wire ancestry, which it never fetches.
        """
        earlier = _fork(5, branch=1)
        extension = _fork(8, branch=1)
        assert self._reason(monkeypatch, earlier, extension) is None
        reason = self._reason(
            monkeypatch, earlier, extension, engine_only=frozenset({5})
        )
        assert reason is not None and "Block(s) 5 of this chain" in reason

    def test_a_rejection_below_the_head_replaces_the_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A rejection below the head is replaced before depth is checked."""
        reason = self._reason(
            monkeypatch,
            _fork(10, branch=1),
            _fork(5, branch=2),
            expects_rejection=True,
        )
        assert reason is not None and "below" in reason


@dataclass
class _HeadRPC:
    """An `EthRPC` whose latest block is `answer`, or which raises it."""

    answer: Any
    opened: list[tuple[str, Any]] = field(default_factory=list)

    def __call__(self, url: str, *, request_timeout: Any) -> "_HeadRPC":
        """Record how the client's RPC was opened."""
        self.opened.append((url, request_timeout))
        return self

    def __enter__(self) -> "_HeadRPC":
        """Open nothing."""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Close nothing."""

    def get_block_by_number(
        self, block_number: int | str = "latest", full_txs: bool = True
    ) -> Any:
        """Answer the latest block."""
        del full_txs
        assert block_number == "latest"
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


class TestClientHeadLookup:
    """How a reused client's head is looked up, and a failed lookup."""

    CLIENT = SimpleNamespace(id="c", ip="10.0.0.2")

    def test_the_head_is_the_latest_block(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The latest block's number and hash, under the lookup timeout."""
        rpc = _HeadRPC({"number": "0x45", "hash": "0x" + "11" * 32})
        monkeypatch.setattr(client_policy, "EthRPC", rpc)
        head = client_policy.client_head(cast(Any, self.CLIENT))
        assert head == (69, bytes.fromhex("11" * 32))
        assert rpc.opened == [("http://10.0.0.2:8545", HEAD_LOOKUP_TIMEOUT)]

    @pytest.mark.parametrize(
        "answer,cause",
        [
            pytest.param(None, "no head block", id="no-block"),
            pytest.param(TimeoutError("no answer"), "no answer", id="timeout"),
        ],
    )
    def test_a_failed_lookup_replaces_the_client(
        self, monkeypatch: pytest.MonkeyPatch, answer: Any, cause: str
    ) -> None:
        """A client that cannot answer for its head is not reused."""
        monkeypatch.setattr(client_policy, "EthRPC", _HeadRPC(answer))
        reason = replacement_reason(
            cast(Any, self.CLIENT),
            cast(Any, SimpleNamespace(chain=_fork(3, branch=2))),
            None,
        )
        assert reason is not None
        assert "lookup failed" in reason and cause in reason


class _DroppedPeer:
    """A group's peer whose client hung up after the previous test."""

    def __init__(self, refusal: Exception | None = None) -> None:
        """Start dead; a redial raises `refusal`, if given."""
        self.alive = False
        self.refusal = refusal
        self.calls: list[str] = []

    def reset_statistics(self) -> None:
        """Record the reset."""
        self.calls.append("reset")

    def reconnect(self, chain: Chain, timeout: float = 30.0) -> None:
        """Record the redial, then refuse it if told to."""
        del chain, timeout
        self.calls.append("redial")
        if self.refusal is not None:
            raise self.refusal


def _mock_peer_for_next_test(peer: _DroppedPeer) -> Any:
    """Run the `mock_peer` fixture for a test of `peer`'s group."""
    case = SimpleNamespace(chain=_chain([_block(1, empty=False)]))
    return fixture_body(wirex.mock_peer)(
        client=SimpleNamespace(id="client"),
        sync_target_cases=[case],
        mock_peers={"client": peer},
        wirex_eth_versions=(),
        wirex_serve_bals=False,
        wirex_fork_schedule=ForkSchedule(),
        total_timing_data=TimingData("Total"),
    )


class TestRedialBetweenTests:
    """The next test of a group redials a peer its client dropped."""

    def test_the_test_statistics_start_before_the_redial(self) -> None:
        """The redialed session's first requests are this test's."""
        peer = _DroppedPeer()
        assert _mock_peer_for_next_test(peer) is peer
        assert peer.calls == ["reset", "redial"]

    @pytest.mark.parametrize(
        "refusal",
        [ConnectionRefusedError("refused"), RLPxError("Disconnect 5")],
        ids=["connection-refused", "disconnect-on-hello"],
    )
    def test_a_refused_redial_is_left_to_the_test(
        self, refusal: Exception
    ) -> None:
        """
        A refused redial does not error the test's setup: the dead peer
        is handed to the test, whose sync loop redials it again.
        """
        peer = _DroppedPeer(refusal)
        assert _mock_peer_for_next_test(peer) is peer
        assert peer.calls == ["reset", "redial"]


POST_MERGE_FORKS = sorted(
    (fork for fork in ALL_FORKS_WITH_TRANSITIONS if fork >= Paris), key=str
)
"""Sorted, so every xdist worker collects the same parameters."""


def _ruleset_activations(fork: Any) -> tuple[set[int], set[int]]:
    """Return the block and time activations Hive configures past 0."""
    entries = ruleset[fork]
    blocks = {
        value
        for key, value in entries.items()
        if key.startswith("HIVE_FORK_") and value
    }
    times = {
        value
        for key, value in entries.items()
        if key.endswith("_TIMESTAMP") and value
    }
    return blocks, times


class TestForkSchedule:
    """The peer's fork schedule is the one the client is configured with."""

    def test_a_transition_fork_activates_its_second_fork_later(
        self,
    ) -> None:
        """ParisToShanghaiAtTime15k forks to Shanghai at t=15000."""
        assert wirex.fork_schedule_of(
            ParisToShanghaiAtTime15k
        ) == ForkSchedule(block_numbers=(0,), timestamps=(15000,))

    def test_a_single_fork_runs_from_genesis(self) -> None:
        """A fork that is no transition schedules nothing past genesis."""
        assert wirex.fork_schedule_of(Cancun) == ForkSchedule()

    @pytest.mark.parametrize("fork", POST_MERGE_FORKS, ids=str)
    def test_the_schedule_matches_the_hive_ruleset(self, fork: Any) -> None:
        """Every activation past genesis the client gets, and no other."""
        schedule = wirex.fork_schedule_of(fork)
        blocks, times = _ruleset_activations(fork)
        assert {n for n in schedule.block_numbers if n} == blocks
        assert {t for t in schedule.timestamps if t} == times

    def test_the_fixture_reads_the_groups_fork(self) -> None:
        """The schedule comes from the pre-allocation group's network."""
        group = SimpleNamespace(fork=ParisToShanghaiAtTime15k)
        schedule = fixture_body(wirex.wirex_fork_schedule)(group)
        assert schedule.timestamps == (15000,)
