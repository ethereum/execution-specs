"""
Tests for the wirex simulator's per-target path resolution.

The scenarios mirror the real fixture shapes the plural `syncPayloads`
contract produces, including the two Osaka EIP-7594 fan-outs and the
Amsterdam EIP-7954/EIP-7981 mixed-validity transitions, using stub
payloads that carry exactly the fields the resolver reads: the declared
block and parent hashes, the declared validation error, and the Engine
API error code.
"""

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, cast

import pytest

from execution_testing.base_types import Hash
from execution_testing.devp2p.chain import ChainReconstructionError
from execution_testing.exceptions import (
    BlockException,
    TransactionException,
)
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import FixtureEngineNewPayload

from ..simulators.wirex import conftest as wirex
from ..simulators.wirex.sync_targets import (
    SyncTargetResolutionError,
    raw_target_path_lengths,
    resolve_sync_paths,
    target_path_lengths,
)
from .direct_calls import fixture_body

GENESIS = Hash(0)
GENESIS_HEADER = SimpleNamespace(block_hash=GENESIS)


@dataclass
class _StubExecutionPayload:
    """The two hash fields ancestry resolution reads."""

    block_hash: Hash
    parent_hash: Hash


@dataclass
class _StubPayload:
    """The payload fields the resolver and its classification read."""

    params: tuple[_StubExecutionPayload, ...]
    validation_error: object = None
    error_code: object = None

    def valid(self) -> bool:
        """Return whether the payload declares no validation error."""
        return self.validation_error is None


def _payload(
    block_hash: int,
    parent_hash: int,
    error: object = None,
    error_code: object = None,
) -> FixtureEngineNewPayload:
    """Return a stub payload linking `block_hash` to `parent_hash`."""
    execution_payload = _StubExecutionPayload(
        Hash(block_hash), Hash(parent_hash)
    )
    return cast(
        FixtureEngineNewPayload,
        _StubPayload(
            params=(execution_payload,),
            validation_error=error,
            error_code=error_code,
        ),
    )


@dataclass
class _StubFixture:
    """The two fixture fields path resolution reads."""

    payloads: list[FixtureEngineNewPayload]
    sync_payloads: list[FixtureEngineNewPayload] | None = None


def _fixture(
    payloads: list[FixtureEngineNewPayload],
    sync_payloads: list[FixtureEngineNewPayload] | None = None,
) -> BlockchainEngineXFixture:
    """Return a fixture carrying exactly the fields the resolver reads."""
    return cast(
        BlockchainEngineXFixture, _StubFixture(payloads, sync_payloads)
    )


def _raw(payload: FixtureEngineNewPayload) -> dict[str, Any]:
    """Return `payload` as the raw JSON the collection pass reads."""
    execution_payload = payload.params[0]
    return {
        "params": [
            {
                "blockHash": str(execution_payload.block_hash),
                "parentHash": str(execution_payload.parent_hash),
            }
        ]
    }


INVALID = TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED
OTHER_INVALID = BlockException.INCORRECT_EXCESS_BLOB_GAS


PayloadSpec = tuple[int, int, object]
"""A stub payload's block hash, parent hash and declared error."""

PathSpec = tuple[tuple[int, ...], bool, set[object]]
"""A path's authored hashes, whether it is a rejection, its errors."""

SHAPES: dict[
    str, tuple[list[PayloadSpec], list[tuple[int, int]], list[PathSpec]]
] = {
    "linear": (
        [(1, 0, None), (2, 1, None)],
        [(3, 2)],
        [((1, 2), False, set())],
    ),
    # The valid target must not inherit its sibling's invalidity.
    "valid-beside-an-invalid-sibling": (
        [(1, 0, INVALID), (2, 0, None)],
        [(3, 1), (4, 2)],
        [((1,), True, {INVALID}), ((2,), False, set())],
    ),
    # EIP-7594 `blob_count_10`: three invalid block-1 siblings.
    "three-invalid-siblings": (
        [(1, 0, INVALID), (2, 0, INVALID), (3, 0, INVALID)],
        [(4, 1), (5, 2), (6, 3)],
        [((n,), True, {INVALID}) for n in (1, 2, 3)],
    ),
    # EIP-7594 `blob_count_7`: one valid block, two invalid leaves.
    "valid-prefix-below-two-invalid-siblings": (
        [(1, 0, None), (2, 1, INVALID), (3, 1, INVALID)],
        [(4, 2), (5, 3)],
        [((1, 2), True, {INVALID}), ((1, 3), True, {INVALID})],
    ),
    # EIP-7981: invalid, valid, invalid, valid directives, so the second
    # invalid payload is a sibling of the second valid one.
    "mixed-validity-leaves": (
        [(1, 0, INVALID), (2, 0, None), (3, 2, OTHER_INVALID), (4, 2, None)],
        [(5, 1), (6, 3), (7, 4)],
        [
            ((1,), True, {INVALID}),
            ((2, 3), True, {OTHER_INVALID}),
            ((2, 4), False, set()),
        ],
    ),
    "shared-trunk": (
        [(1, 0, None), (2, 1, INVALID), (3, 1, None)],
        [(4, 2), (5, 3)],
        [((1, 2), True, {INVALID}), ((1, 3), False, set())],
    ),
}
"""
The real fixture shapes the plural `syncPayloads` contract produces:
each shape's payloads, its targets, and the path each target selects.
"""


def _shape(
    name: str,
) -> tuple[list[FixtureEngineNewPayload], list[FixtureEngineNewPayload]]:
    """Return the stub payloads and targets of the shape `name`."""
    payloads, targets, _ = SHAPES[name]
    return (
        [_payload(*spec) for spec in payloads],
        [_payload(*spec) for spec in targets],
    )


@pytest.mark.parametrize("name", SHAPES)
def test_each_target_selects_its_own_path(name: str) -> None:
    """
    Each path re-resolves its full ancestry from its own leaf, in target
    order, and is a rejection only when a payload on it is invalid.
    Shared ancestors are the same authored objects on every path, and
    no authored payload is left off all of them.
    """
    payloads, targets = _shape(name)
    by_hash = {payload.params[0].block_hash: payload for payload in payloads}
    paths = resolve_sync_paths(GENESIS, _fixture(payloads, targets))
    assert len(paths) == len(SHAPES[name][2])
    for index, (path, target, (hashes, rejected, errors)) in enumerate(
        zip(paths, targets, SHAPES[name][2], strict=True)
    ):
        authored = tuple(by_hash[Hash(number)] for number in hashes)
        assert (path.index, path.target) == (index, target)
        assert all(
            ours is theirs
            for ours, theirs in zip(path.authored, authored, strict=True)
        )
        assert path.announces_scaffolding
        assert path.served_payloads == [*authored, target]
        assert path.length == len(hashes) + 1
        assert path.expects_rejection == rejected
        assert path.invalidities == errors
    covered = {id(payload) for path in paths for payload in path.authored}
    assert covered == {id(payload) for payload in payloads}


class TestDiagnostics:
    """Corpus defects fail loudly, naming the target."""

    def test_missing_parent(self) -> None:
        """A parent that is neither genesis nor authored is named."""
        fixture = _fixture([_payload(1, 0)], [_payload(2, 9)])
        with pytest.raises(
            SyncTargetResolutionError, match="target 1/1 descends from"
        ):
            resolve_sync_paths(GENESIS, fixture)

    def test_duplicate_authored_hash(self) -> None:
        """Two authored payloads with one hash cannot be told apart."""
        fixture = _fixture([_payload(1, 0), _payload(1, 0)], [_payload(2, 1)])
        with pytest.raises(
            SyncTargetResolutionError, match="two authored payloads"
        ):
            resolve_sync_paths(GENESIS, fixture)

    def test_cycle(self) -> None:
        """An ancestry that revisits a hash is a cycle, not a chain."""
        fixture = _fixture([_payload(1, 2), _payload(2, 1)], [_payload(3, 1)])
        with pytest.raises(SyncTargetResolutionError, match="cycles at"):
            resolve_sync_paths(GENESIS, fixture)

    def test_target_directly_above_genesis(self) -> None:
        """A target must sit above an authored leaf, never genesis."""
        fixture = _fixture([_payload(1, 0)], [_payload(2, 0)])
        with pytest.raises(
            SyncTargetResolutionError, match="directly above genesis"
        ):
            resolve_sync_paths(GENESIS, fixture)


class TestNoTargetFallback:
    """Fixtures without targets announce their own authored head."""

    @pytest.mark.parametrize(
        "sync_payloads", [None, []], ids=["none", "empty"]
    )
    def test_bare_chain_is_served_as_written(
        self, sync_payloads: list[FixtureEngineNewPayload] | None
    ) -> None:
        """Error-code, opted-out and --no-sync-block chains: one path."""
        authored = [_payload(1, 0), _payload(2, 1)]
        (path,) = resolve_sync_paths(
            GENESIS, _fixture(authored, sync_payloads)
        )
        assert path.target is authored[-1]
        assert path.authored == tuple(authored)
        assert not path.announces_scaffolding
        assert path.served_payloads == authored
        assert path.length == 2

    def test_error_code_head_expects_rejection(self) -> None:
        """A declared Engine API error code is itself a rejection."""
        head = _payload(1, 0, error_code=-32602)
        (path,) = resolve_sync_paths(GENESIS, _fixture([head], None))
        assert path.expects_rejection

    def test_fixture_wide_invalidity_applies_to_the_bare_path(self) -> None:
        """With one path, the whole fixture is the path."""
        authored = [_payload(1, 0), _payload(2, 1, error=INVALID)]
        (path,) = resolve_sync_paths(GENESIS, _fixture(authored, None))
        assert path.expects_rejection
        assert path.invalidities == {INVALID}

    def test_bare_siblings_resolve_to_one_path_per_leaf(self) -> None:
        """
        A valid block after an invalid one is its sibling, so each leaf
        is announced on its own path, judged by its own validity.
        """
        trunk = _payload(1, 0)
        invalid, sibling = _payload(2, 1, error=INVALID), _payload(3, 1)
        first, second = resolve_sync_paths(
            GENESIS, _fixture([trunk, invalid, sibling], None)
        )
        assert (first.target, first.authored) == (invalid, (trunk, invalid))
        assert (second.target, second.authored) == (sibling, (trunk, sibling))
        assert first.expects_rejection and not second.expects_rejection
        assert {first.total, second.total} == {2}
        assert not first.announces_scaffolding
        assert not second.announces_scaffolding

    def test_a_bare_leaf_off_genesis_is_refused(self) -> None:
        """A bare ancestry that never reaches genesis is a corpus defect."""
        with pytest.raises(SyncTargetResolutionError, match="leaf 1/1"):
            resolve_sync_paths(GENESIS, _fixture([_payload(2, 1)], None))


class TestDeclaredInvalidities:
    """The census the per-class body downgrade is decided by."""

    def test_single_and_listed_exceptions_are_collected(self) -> None:
        """One declared exception or a pipe-list both count."""
        authored = [
            _payload(1, 0),
            _payload(2, 1, error=OTHER_INVALID),
            _payload(3, 2, error=[INVALID]),
        ]
        (path,) = resolve_sync_paths(GENESIS, _fixture(authored, None))
        assert path.invalidities == {INVALID, OTHER_INVALID}


class TestPathLengths:
    """The per-target lengths that gate min-blocks and sort collection."""

    @pytest.mark.parametrize(
        "shape,expected",
        [
            # Four directives, three targets: lengths are per ancestry.
            pytest.param("mixed-validity-leaves", [2, 3, 3], id="targets"),
            # Without targets the served chain is the authored one.
            pytest.param(None, [1], id="bare"),
        ],
    )
    def test_lengths_follow_each_path(
        self, shape: str | None, expected: list[int]
    ) -> None:
        """The model, the collection-time raw read and the paths agree."""
        payloads: list[FixtureEngineNewPayload]
        targets: list[FixtureEngineNewPayload]
        if shape is None:
            payloads, targets = [_payload(1, 0)], []
        else:
            payloads, targets = _shape(shape)
        fixture = _fixture(payloads, targets or None)
        raw = {
            "engineNewPayloads": [_raw(payload) for payload in payloads],
            "syncPayloads": [_raw(target) for target in targets],
        }
        assert target_path_lengths(fixture) == expected
        assert raw_target_path_lengths(raw) == expected
        paths = resolve_sync_paths(GENESIS, fixture)
        assert [path.length for path in paths] == expected

    def test_raw_anomaly_ends_the_walk_instead_of_raising(self) -> None:
        """Collection survives a defect the test will diagnose later."""
        raw = {
            "engineNewPayloads": [
                {"params": [{"blockHash": "0xa1", "parentHash": "0xa2"}]},
                {"params": [{"blockHash": "0xa2", "parentHash": "0xa1"}]},
            ],
            "syncPayloads": [
                {"params": [{"blockHash": "0xs1", "parentHash": "0xa1"}]},
            ],
        }
        assert raw_target_path_lengths(raw) == [3]


UNDECODABLE = TransactionException.TYPE_3_TX_CONTRACT_CREATION


class TestSyncTargetCases:
    """Which of a fixture's paths the `sync_target_cases` fixture runs."""

    @staticmethod
    def _cases(
        monkeypatch: pytest.MonkeyPatch,
        fixture: BlockchainEngineXFixture,
        min_blocks: int = 2,
        fails: Callable[[list[Any]], bool] | None = None,
        unrebuildable: Callable[[Any], bool] | None = None,
    ) -> tuple[list[Any], list[list[Any]]]:
        """
        Return the fixture's runnable cases and every chain rebuilt.

        Chain reconstruction is replaced by a stand-in that returns the
        payloads it was given, or raises when `fails` says so. A single
        block rebuilds unless `unrebuildable` says it does not.
        """
        rebuilt: list[list[Any]] = []

        def block_from_payload(payload: Any) -> Any:
            if unrebuildable is not None and unrebuildable(payload):
                raise ChainReconstructionError("commitment modified at fill")
            return payload

        monkeypatch.setattr(wirex, "block_from_payload", block_from_payload)

        def chain_from_payloads(genesis: Any, payloads: list[Any]) -> Any:
            assert genesis is GENESIS_HEADER
            rebuilt.append(payloads)
            if fails is not None and fails(payloads):
                raise ChainReconstructionError("commitment modified at fill")
            return payloads

        monkeypatch.setattr(wirex, "chain_from_payloads", chain_from_payloads)
        cases = fixture_body(wirex.sync_target_cases)(
            GENESIS_HEADER, fixture, min_blocks
        )
        return cases, rebuilt

    def test_a_chain_below_the_minimum_skips(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A one-block bare chain puts nothing on the wire at minimum 2."""
        fixture = _fixture([_payload(1, 0)], None)
        with pytest.raises(pytest.skip.Exception, match="1 block"):
            self._cases(monkeypatch, fixture, min_blocks=2)

    def test_a_chain_at_the_minimum_runs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The same chain runs once the minimum allows it."""
        authored = [_payload(1, 0)]
        (case,), rebuilt = self._cases(
            monkeypatch, _fixture(authored, None), min_blocks=1
        )
        assert rebuilt == [authored]
        assert case.chain == authored

    def test_an_undecodable_path_drops_beside_a_decodable_one(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A body no client decodes drops its path, not its sibling's."""
        undecodable, valid = _payload(1, 0, error=UNDECODABLE), _payload(2, 0)
        kept = _payload(4, 2)
        fixture = _fixture([undecodable, valid], [_payload(3, 1), kept])
        (case,), rebuilt = self._cases(monkeypatch, fixture)
        assert case.path.target is kept
        assert rebuilt == [[valid, kept]]

    def test_an_unrebuildable_invalid_path_drops(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An invalid path whose header cannot be rebuilt is omitted."""
        invalid, valid = _payload(1, 0, error=INVALID), _payload(2, 0)
        kept = _payload(4, 2)
        fixture = _fixture([invalid, valid], [_payload(3, 1), kept])
        (case,), _ = self._cases(
            monkeypatch,
            fixture,
            fails=lambda payloads: invalid in payloads,
            unrebuildable=lambda payload: payload is invalid,
        )
        assert case.path.target is kept

    def test_another_failure_on_an_invalid_path_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        An invalid path whose own invalid header rebuilds but whose chain
        does not is a defect, not a skip.
        """
        invalid, valid = _payload(1, 0, error=INVALID), _payload(2, 0)
        fixture = _fixture([invalid, valid], [_payload(3, 1), _payload(4, 2)])
        with pytest.raises(ChainReconstructionError):
            self._cases(
                monkeypatch,
                fixture,
                fails=lambda payloads: invalid in payloads,
            )

    def test_an_unrebuildable_valid_path_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A valid path that cannot be rebuilt is a defect, not a skip."""
        invalid, valid = _payload(1, 0, error=INVALID), _payload(2, 0)
        fixture = _fixture([invalid, valid], [_payload(3, 1), _payload(4, 2)])
        with pytest.raises(ChainReconstructionError):
            self._cases(
                monkeypatch, fixture, fails=lambda payloads: valid in payloads
            )
