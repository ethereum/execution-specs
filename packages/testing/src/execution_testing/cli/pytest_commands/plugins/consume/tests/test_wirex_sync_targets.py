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
from typing import cast

import pytest

from execution_testing.base_types import Hash
from execution_testing.exceptions import (
    BlockException,
    TransactionException,
)
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import FixtureEngineNewPayload

from ..simulators.wirex.sync_targets import (
    HEADER_JUDGEABLE_INVALIDITIES,
    UNDECODABLE_BODY_INVALIDITIES,
    SyncTargetResolutionError,
    raw_target_path_lengths,
    resolve_sync_paths,
    target_path_lengths,
)

GENESIS = Hash(0)


def test_fixture_schema_retains_plural_sync_payloads() -> None:
    """The consume-side model must not discard the fill-side targets."""
    field = BlockchainEngineXFixture.model_fields["sync_payloads"]
    assert field.alias == "syncPayloads"


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

        This is the shape fixture-wide `any(not payload.valid())`
        misclassifies: the fixture contains an invalid payload, but
        the valid target's path does not.
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


class TestMixedValidityLeaves:
    """The EIP-7981 shape: invalid, valid, invalid, valid directives."""

    def test_two_invalid_leaves_and_a_final_valid_leaf(self) -> None:
        """
        Three targets: the rejected branches first, the valid one last.

        The two valid payloads chain (the second invalid payload is a
        sibling of the second valid one), so the final target's path
        is the two valid payloads and expects a successful sync.
        """
        invalid_one = _payload(1, 0, error=INVALID)
        valid_one = _payload(2, 0)
        invalid_two = _payload(3, 2, error=OTHER_INVALID)
        valid_two = _payload(4, 2)
        targets = [_payload(5, 1), _payload(6, 3), _payload(7, 4)]
        paths = resolve_sync_paths(
            GENESIS,
            _fixture(
                [invalid_one, valid_one, invalid_two, valid_two], targets
            ),
        )
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
        payloads = [
            _payload(1, 0, error=INVALID),
            _payload(2, 0),
            _payload(3, 2, error=OTHER_INVALID),
            _payload(4, 2),
        ]
        targets = [_payload(5, 1), _payload(6, 3), _payload(7, 4)]
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

    def test_bare_chain_is_served_as_written(self) -> None:
        """Error-code, opted-out and --no-sync-block chains: one path."""
        authored = [_payload(1, 0), _payload(2, 1)]
        (path,) = resolve_sync_paths(GENESIS, _fixture(authored, None))
        assert path.target is authored[-1]
        assert path.authored == tuple(authored)
        assert not path.announces_scaffolding
        assert path.served_payloads == authored
        assert path.length == 2

    def test_an_empty_target_list_is_the_same_as_none(self) -> None:
        """The schema default and an explicit empty list agree."""
        authored = [_payload(1, 0)]
        (path,) = resolve_sync_paths(GENESIS, _fixture(authored, []))
        assert not path.announces_scaffolding

    def test_error_code_head_expects_rejection(self) -> None:
        """A declared Engine API error code is itself a rejection."""
        head = _payload(1, 0, error_code=-32602)
        (path,) = resolve_sync_paths(GENESIS, _fixture([head], None))
        assert path.expects_rejection

    def test_fixture_wide_invalidity_applies_to_the_bare_path(self) -> None:
        """With one path, path-local equals the old fixture-wide read."""
        authored = [_payload(1, 0), _payload(2, 1, error=INVALID)]
        (path,) = resolve_sync_paths(GENESIS, _fixture(authored, None))
        assert path.expects_rejection
        assert path.invalidities == {INVALID}


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

    def test_the_undecodable_and_judgeable_sets_are_disjoint(self) -> None:
        """
        No invalidity is both header-judgeable and undecodable.

        The two sets pull in opposite directions - one relaxes what a
        client must fetch, the other says the block cannot travel at
        all - so an exception in both would make the simulator's
        treatment of it depend on evaluation order.
        """
        assert not (
            HEADER_JUDGEABLE_INVALIDITIES & UNDECODABLE_BODY_INVALIDITIES
        )


class TestPathLengths:
    """The per-target lengths that gate min-blocks and sort collection."""

    def test_lengths_follow_each_path_not_the_directive_count(self) -> None:
        """Four directives, three targets: lengths are per ancestry."""
        payloads = [
            _payload(1, 0, error=INVALID),
            _payload(2, 0),
            _payload(3, 2, error=OTHER_INVALID),
            _payload(4, 2),
        ]
        targets = [_payload(5, 1), _payload(6, 3), _payload(7, 4)]
        fixture = _fixture(payloads, targets)
        assert target_path_lengths(fixture) == [2, 3, 3]
        paths = resolve_sync_paths(GENESIS, fixture)
        assert [path.length for path in paths] == [2, 3, 3]

    def test_bare_fixture_length_is_the_authored_count(self) -> None:
        """Without targets the served chain is the authored one."""
        assert target_path_lengths(_fixture([_payload(1, 0)], None)) == [1]

    def test_raw_lengths_agree_with_the_model(self) -> None:
        """The collection-time raw read matches the parsed one."""
        raw = {
            "engineNewPayloads": [
                {
                    "params": [
                        {"blockHash": "0xa1", "parentHash": "0xg"},
                    ],
                    "validationError": "TransactionException.X",
                },
                {"params": [{"blockHash": "0xa2", "parentHash": "0xg"}]},
            ],
            "syncPayloads": [
                {"params": [{"blockHash": "0xs1", "parentHash": "0xa1"}]},
                {"params": [{"blockHash": "0xs2", "parentHash": "0xa2"}]},
            ],
        }
        assert raw_target_path_lengths(raw) == [2, 2]

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
