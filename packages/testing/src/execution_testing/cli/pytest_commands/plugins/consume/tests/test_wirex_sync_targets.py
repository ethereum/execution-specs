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


class TestLinearChain:
    """A linear valid chain with one target: the singular shape."""

    def test_one_target_selects_the_whole_chain(self) -> None:
        """The single target's path is every authored payload."""
        authored = [_payload(1, 0), _payload(2, 1)]
        target = _payload(3, 2)
        paths = resolve_sync_paths(GENESIS, _fixture(authored, [target]))
        assert len(paths) == 1
        (path,) = paths
        assert path.authored == tuple(authored)
        assert path.target is target
        assert path.announces_scaffolding
        assert path.served_payloads == [*authored, target]
        assert path.length == 3
        assert not path.expects_rejection


class TestPathLocalRejection:
    """Invalid and valid siblings: rejection is a path property."""

    def test_a_valid_branch_beside_an_invalid_sibling(self) -> None:
        """
        The valid target must not inherit its sibling's invalidity.

        The fixture contains an invalid payload; the valid target's path
        does not.
        """
        invalid = _payload(1, 0, error=INVALID)
        valid = _payload(2, 0)
        targets = [_payload(3, 1), _payload(4, 2)]
        paths = resolve_sync_paths(
            GENESIS, _fixture([invalid, valid], targets)
        )
        rejected, synced = paths
        assert rejected.authored == (invalid,)
        assert rejected.expects_rejection
        assert rejected.invalidities == {INVALID}
        assert synced.authored == (valid,)
        assert not synced.expects_rejection
        assert synced.invalidities == set()


class TestOsakaShapes:
    """The two real pre-Amsterdam fan-outs, from EIP-7594."""

    def test_three_invalid_siblings(self) -> None:
        """`blob_count_10`: three invalid block-1 siblings, 3 targets."""
        siblings = [
            _payload(1, 0, error=INVALID),
            _payload(2, 0, error=INVALID),
            _payload(3, 0, error=INVALID),
        ]
        targets = [_payload(4, 1), _payload(5, 2), _payload(6, 3)]
        paths = resolve_sync_paths(GENESIS, _fixture(siblings, targets))
        assert len(paths) == 3
        for path, sibling in zip(paths, siblings, strict=True):
            assert path.authored == (sibling,)
            assert path.expects_rejection
            assert path.length == 2

    def test_valid_prefix_below_two_invalid_siblings(self) -> None:
        """`blob_count_7`: one valid block, two invalid block-2 leaves."""
        valid = _payload(1, 0)
        siblings = [
            _payload(2, 1, error=INVALID),
            _payload(3, 1, error=INVALID),
        ]
        targets = [_payload(4, 2), _payload(5, 3)]
        paths = resolve_sync_paths(
            GENESIS, _fixture([valid, *siblings], targets)
        )
        assert len(paths) == 2
        for path, sibling in zip(paths, siblings, strict=True):
            assert path.authored == (valid, sibling)
            assert path.expects_rejection
            assert path.length == 3


def _mixed_validity() -> tuple[
    list[FixtureEngineNewPayload], list[FixtureEngineNewPayload]
]:
    """
    Return the EIP-7981 shape's payloads and targets.

    Invalid, valid, invalid, valid directives: the second invalid
    payload is a sibling of the second valid one, so three targets sit
    above the leaves, the valid one last.
    """
    payloads = [
        _payload(1, 0, error=INVALID),
        _payload(2, 0),
        _payload(3, 2, error=OTHER_INVALID),
        _payload(4, 2),
    ]
    targets = [_payload(5, 1), _payload(6, 3), _payload(7, 4)]
    return payloads, targets


class TestMixedValidityLeaves:
    """The EIP-7981 shape: invalid, valid, invalid, valid directives."""

    def test_two_invalid_leaves_and_a_final_valid_leaf(self) -> None:
        """The rejected branches first, then the two valid payloads."""
        payloads, targets = _mixed_validity()
        invalid_one, valid_one, invalid_two, valid_two = payloads
        paths = resolve_sync_paths(GENESIS, _fixture(payloads, targets))
        first, second, third = paths
        assert first.authored == (invalid_one,)
        assert first.expects_rejection
        assert first.invalidities == {INVALID}
        assert second.authored == (valid_one, invalid_two)
        assert second.expects_rejection
        assert second.invalidities == {OTHER_INVALID}
        assert third.authored == (valid_one, valid_two)
        assert not third.expects_rejection
        assert third.invalidities == set()

    def test_every_authored_payload_is_on_some_path(self) -> None:
        """Across all targets, no representable payload is orphaned."""
        payloads, targets = _mixed_validity()
        paths = resolve_sync_paths(GENESIS, _fixture(payloads, targets))
        covered = {id(payload) for path in paths for payload in path.authored}
        assert covered == {id(payload) for payload in payloads}


class TestSharedPrefixes:
    """Shared prefixes reconstruct independently, in target order."""

    def test_paths_are_independent_and_ordered(self) -> None:
        """Each path re-resolves its full ancestry from its own leaf."""
        trunk = _payload(1, 0)
        leaf_one = _payload(2, 1, error=INVALID)
        leaf_two = _payload(3, 1)
        targets = [_payload(4, 2), _payload(5, 3)]
        paths = resolve_sync_paths(
            GENESIS, _fixture([trunk, leaf_one, leaf_two], targets)
        )
        assert [path.index for path in paths] == [0, 1]
        assert [path.target for path in paths] == targets
        assert paths[0].authored == (trunk, leaf_one)
        assert paths[1].authored == (trunk, leaf_two)
        # The shared trunk appears on both paths, as its own object.
        assert paths[0].authored[0] is paths[1].authored[0]


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

    def test_lengths_follow_each_path_not_the_directive_count(self) -> None:
        """Four directives, three targets: lengths are per ancestry."""
        fixture = _fixture(*_mixed_validity())
        assert target_path_lengths(fixture) == [2, 3, 3]
        paths = resolve_sync_paths(GENESIS, fixture)
        assert [path.length for path in paths] == [2, 3, 3]

    def test_bare_fixture_length_is_the_authored_count(self) -> None:
        """Without targets the served chain is the authored one."""
        assert target_path_lengths(_fixture([_payload(1, 0)], None)) == [1]

    def test_raw_lengths_agree_with_the_model(self) -> None:
        """The collection-time raw read matches the parsed one."""
        payloads, targets = _mixed_validity()
        fixture = _fixture(payloads, targets)
        raw = {
            "engineNewPayloads": [_raw(payload) for payload in payloads],
            "syncPayloads": [_raw(target) for target in targets],
        }
        assert raw_target_path_lengths(raw) == target_path_lengths(fixture)
        assert target_path_lengths(fixture) == [2, 3, 3]

    def test_raw_bare_fixture_counts_authored_payloads(self) -> None:
        """A raw fixture without targets keeps its authored length."""
        raw = {
            "engineNewPayloads": [
                {"params": [{"blockHash": "0xa1", "parentHash": "0xg"}]},
            ],
        }
        assert raw_target_path_lengths(raw) == [1]

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
