"""
Resolution of the served chain behind each announced sync target.

An engine_x fixture's payloads need not form one chain: an
expected-invalid payload does not advance the filler's canonical
parent, so a valid payload following it is its sibling. The filler
therefore builds one sync payload above every leaf (the ordered
`syncPayloads` list). Each selects one root-to-leaf path by hash alone:
the target's `parentHash` names its leaf, and authored `parentHash`
links lead back to genesis. List position, timestamps and
`lastblockhash` are never consulted.

Validity is a property of the path, not the fixture: every rejection
expectation and invalidity census here is taken over one path's
payloads, so a sibling's invalidity never affects another path.
"""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Callable, Mapping, TypeVar

from hive.client import Client

from execution_testing.base_types import Hash
from execution_testing.devp2p.chain import Chain
from execution_testing.devp2p.peer import MockPeer
from execution_testing.exceptions import (
    BlockException,
    TransactionException,
)
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import FixtureEngineNewPayload
from execution_testing.rpc import EngineRPC, EthRPC

HEADER_JUDGEABLE_INVALIDITIES: frozenset[
    BlockException | TransactionException
] = frozenset({BlockException.INCORRECT_EXCESS_BLOB_GAS})
"""
Declared invalidities a client can judge from headers alone.

A client may reject such a chain during header validation without
fetching a body (geth does, for `INCORRECT_EXCESS_BLOB_GAS`), so for
these classes the coverage check requires headers only. Entries are
per exception class, never per client, and need measured evidence.
"""


UNDECODABLE_BODY_INVALIDITIES: frozenset[
    BlockException | TransactionException
] = frozenset(
    {
        BlockException.RLP_STRUCTURES_ENCODING,
        TransactionException.TYPE_3_TX_CONTRACT_CREATION,
        TransactionException.TYPE_4_TX_CONTRACT_CREATION,
    }
)
"""
Declared invalidities that leave a block with no wire representation.

No conformant client can decode such a body (a typed transaction
without its mandatory `to`, or malformed RLP): it discards the response
as malformed instead of judging the block, so no verdict arrives. The
Engine API carries these blocks, since a payload lists its transactions
individually, so they run under the Engine simulators and are dropped
here.
"""


class SyncTargetResolutionError(Exception):
    """
    Raised when a target's authored ancestry cannot be resolved.

    The fill side guarantees resolvable ancestry, so this is a corpus
    defect, and the test fails rather than skips.
    """


def _block_hash(payload: FixtureEngineNewPayload) -> Hash:
    """Return the block hash `payload` declares."""
    return payload.params[0].block_hash


def _parent_hash(payload: FixtureEngineNewPayload) -> Hash:
    """Return the parent hash `payload` declares."""
    return payload.params[0].parent_hash


@dataclass(frozen=True)
class SyncPath:
    """
    One announced sync target and the authored path it selects.

    The served chain is the authored path plus the target when the
    target is a framework sync payload, and the authored path alone
    when a fixture without targets announces its own head.
    """

    index: int
    """Position of this target in the fixture's announcement order."""

    total: int
    """How many targets the fixture announces."""

    target: FixtureEngineNewPayload
    """The payload announced as the sync target."""

    authored: tuple[FixtureEngineNewPayload, ...]
    """The authored payloads on this path, ancestor-first."""

    announces_scaffolding: bool
    """Whether the target is a framework sync payload above the leaf."""

    @property
    def served_payloads(self) -> list[FixtureEngineNewPayload]:
        """Return the payloads of the served chain, ancestor-first."""
        if self.announces_scaffolding:
            return [*self.authored, self.target]
        return list(self.authored)

    @property
    def length(self) -> int:
        """Return the served chain's block count."""
        return len(self.authored) + (1 if self.announces_scaffolding else 0)

    @property
    def expects_rejection(self) -> bool:
        """
        Return whether this path passes by the client refusing it.

        A target declaring an Engine API error code is a rejection too.
        """
        return (
            any(not payload.valid() for payload in self.served_payloads)
            or self.target.error_code is not None
        )

    @property
    def checks_wire_coverage(self) -> bool:
        """
        Return whether a run of this path asserts its wire coverage.

        A valid path always does. A rejection does only when it
        announces a framework sync payload: without one the client may
        judge the announced head without fetching an ancestor.
        """
        return not self.expects_rejection or self.announces_scaffolding

    @property
    def expected_latest_valid_hash(self) -> Hash | None:
        """
        Return the `latestValidHash` an INVALID verdict on this path owes.

        It is the parent of the first invalid payload on the served
        chain, the newest block the client should still hold valid, even
        when a framework sync target sits above the invalid block. Return
        `None` when no served payload is invalid (a path rejected only by
        its declared Engine API error code).
        """
        for payload in self.served_payloads:
            if not payload.valid():
                return _parent_hash(payload)
        return None

    @property
    def invalidities(self) -> set[BlockException | TransactionException]:
        """Return every exception this path's payloads declare."""
        invalidities: set[BlockException | TransactionException] = set()
        for payload in self.served_payloads:
            error = payload.validation_error
            if error is None:
                continue
            if isinstance(error, list):
                invalidities.update(error)
            else:
                invalidities.add(error)
        return invalidities

    @property
    def name(self) -> str:
        """Return the short name failure messages prefix this path by."""
        return f"target {self.index + 1}/{self.total}"

    @property
    def label(self) -> str:
        """Return the name logs and failures identify this path by."""
        leaf = _block_hash(self.authored[-1])
        return f"{self.name} above leaf {leaf}"


@dataclass(frozen=True)
class SyncTargetCase:
    """
    One runnable sync target: its path and the reconstructed chain.

    The `chain` is the path's `served_payloads` rebuilt into servable
    blocks, so `chain.head` is the announced target and every block
    below it is the wire-owed ancestry.
    """

    path: SyncPath
    chain: Chain


@dataclass(frozen=True)
class TargetContext:
    """Everything one sync target needs to talk to its own client."""

    client: Client
    eth_rpc: EthRPC
    engine_rpc: EngineRPC
    mock_peer: MockPeer


TargetContextFactory = Callable[
    [SyncTargetCase], AbstractContextManager[TargetContext]
]
"""Open the context a sync target after the first runs in."""


def resolve_sync_paths(
    genesis_hash: Hash, fixture: BlockchainEngineXFixture
) -> list[SyncPath]:
    """
    Return the served path behind each of the fixture's sync targets.

    A fixture without targets (a chain asserting an Engine API error
    code, one whose leaves admit no child block, one that opted out
    with `sync_block=False`, or a fill with `--no-sync-block`) yields
    one path per authored leaf, a payload no other payload builds on:
    the leaf's ancestry, announced by the leaf itself. A linear fixture
    has one leaf, its last payload, and a valid payload after an
    invalid one is its sibling, so it is a leaf of its own.

    Raise `SyncTargetResolutionError` when an ancestry does not reach
    `genesis_hash` through authored payloads.
    """
    payloads_by_hash: dict[Hash, FixtureEngineNewPayload] = {}
    for payload in fixture.payloads:
        block_hash = _block_hash(payload)
        if block_hash in payloads_by_hash:
            raise SyncTargetResolutionError(
                f"two authored payloads declare block hash {block_hash}; "
                "hash-based ancestry cannot tell them apart"
            )
        payloads_by_hash[block_hash] = payload

    def ancestry(name: str, parent: Hash) -> list[FixtureEngineNewPayload]:
        """Return the authored payloads from genesis up to `parent`."""
        authored: list[FixtureEngineNewPayload] = []
        visited: set[Hash] = set()
        current = parent
        while current != genesis_hash:
            if current in visited:
                raise SyncTargetResolutionError(
                    f"{name}'s authored ancestry cycles at {current}"
                )
            visited.add(current)
            ancestor = payloads_by_hash.get(current)
            if ancestor is None:
                raise SyncTargetResolutionError(
                    f"{name} descends from {current}, which is neither "
                    "genesis nor an authored payload"
                )
            authored.append(ancestor)
            current = _parent_hash(ancestor)
        authored.reverse()
        return authored

    targets = fixture.sync_payloads
    if not targets:
        parents = {_parent_hash(payload) for payload in fixture.payloads}
        leaves = [
            payload
            for payload in fixture.payloads
            if _block_hash(payload) not in parents
        ]
        return [
            SyncPath(
                index=index,
                total=len(leaves),
                target=leaf,
                authored=(
                    *ancestry(
                        f"leaf {index + 1}/{len(leaves)}", _parent_hash(leaf)
                    ),
                    leaf,
                ),
                announces_scaffolding=False,
            )
            for index, leaf in enumerate(leaves)
        ]

    paths: list[SyncPath] = []
    total = len(targets)
    for index, target in enumerate(targets):
        name = f"sync target {index + 1}/{total}"
        authored = ancestry(name, _parent_hash(target))
        if not authored:
            raise SyncTargetResolutionError(
                f"{name} sits directly above genesis and selects no "
                "authored payload"
            )
        paths.append(
            SyncPath(
                index=index,
                total=total,
                target=target,
                authored=tuple(authored),
                announces_scaffolding=True,
            )
        )
    return paths


LinkKey = TypeVar("LinkKey", Hash, str)


def _path_lengths_from_links(
    parent_by_hash: dict[LinkKey, LinkKey],
    target_parents: list[LinkKey],
) -> list[int]:
    """
    Return each target's served-chain length from parent links alone.

    Used at collection time, without the group's genesis hash: the
    walk stops at the first unknown hash, and an anomaly ends it early
    instead of raising, so the length is then a lower bound.
    """
    lengths: list[int] = []
    for parent in target_parents:
        depth = 0
        visited: set[LinkKey] = set()
        current = parent
        while current in parent_by_hash and current not in visited:
            visited.add(current)
            depth += 1
            current = parent_by_hash[current]
        lengths.append(depth + 1)  # the target itself
    return lengths


def target_path_lengths(fixture: BlockchainEngineXFixture) -> list[int]:
    """
    Return each served chain's length for an already-parsed fixture.

    One entry per sync target, or the authored payload count alone for
    a fixture without targets.
    """
    targets = fixture.sync_payloads
    if not targets:
        return [len(fixture.payloads)]
    parent_by_hash = {
        _block_hash(payload): _parent_hash(payload)
        for payload in fixture.payloads
    }
    return _path_lengths_from_links(
        parent_by_hash, [_parent_hash(target) for target in targets]
    )


def raw_target_path_lengths(raw_fixture: Mapping[str, Any]) -> list[int]:
    """
    Return each served chain's length from a raw fixture dictionary.

    The collection-time counterpart of `target_path_lengths`, for the
    ordering pass that reads fixture files without model validation.
    """
    payloads = raw_fixture.get("engineNewPayloads", [])
    targets = raw_fixture.get("syncPayloads") or []
    if not targets:
        return [len(payloads)]
    parent_by_hash = {
        payload["params"][0]["blockHash"]: payload["params"][0]["parentHash"]
        for payload in payloads
    }
    return _path_lengths_from_links(
        parent_by_hash,
        [target["params"][0]["parentHash"] for target in targets],
    )
