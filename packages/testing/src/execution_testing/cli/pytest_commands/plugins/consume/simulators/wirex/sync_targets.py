"""
Resolution of the served chain behind each announced sync target.

An engine_x fixture's `engineNewPayloads` is a sequence of Engine API
directives, not necessarily one linear chain: an expected-invalid
payload does not advance the filler's canonical parent, so a valid
payload following it is its sibling. The filler therefore emits one
framework-built sync payload above every leaf of the authored payload
graph - each entry of the optional ordered `syncPayloads` list - and a
sync-based consumer must exercise every one of them.

Each target selects exactly one root-to-leaf path through the authored
payloads. Topology comes only from hashes: the target's `parentHash`
names its authored leaf, and following authored `parentHash` links
backwards reaches genesis. List position, timestamps and
`lastblockhash` say nothing about ancestry and are never consulted.
Sibling payloads never share a resolved path, so each path is a linear
chain a mock peer can serve.

Validity is a property of the path, not the fixture: a valid target's
path can coexist with an invalid sibling elsewhere in the fixture, so
every rejection expectation and declared-invalidity census here is
taken over one path's payloads only.
"""

from dataclasses import dataclass

from execution_testing.base_types import Hash
from execution_testing.exceptions import (
    BlockException,
    TransactionException,
)
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import FixtureEngineNewPayload


class SyncTargetResolutionError(Exception):
    """
    Raised when a target's authored ancestry cannot be resolved.

    This is a corpus defect, never a client behavior: the fill side
    guarantees that every target's `parentHash` names an authored
    payload and that authored `parentHash` links reach genesis, so a
    missing parent, a duplicate authored block hash, or a cycle means
    the fixture violates its own contract and the test must fail
    loudly rather than skip.
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

    `authored` holds the authored payloads on the target's ancestry
    path, ancestor-first; `target` is the payload announced over the
    Engine API. When the target is framework scaffolding
    (`announces_scaffolding`), it rides above the path's leaf and the
    served chain is the authored path plus the target; a fixture
    without targets announces its own authored head, which is already
    the last authored payload, so the served chain is the authored
    path alone.
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

        Decided over this path's payloads only: a path containing a
        declared-invalid payload must be judged INVALID once its
        ancestry has arrived, and a target declaring an Engine API
        error code is itself a rejection. An invalid sibling on
        another path says nothing about this one.
        """
        return (
            any(not payload.valid() for payload in self.served_payloads)
            or self.target.error_code is not None
        )

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
    def label(self) -> str:
        """Return the name logs and failures identify this path by."""
        leaf = _block_hash(self.authored[-1])
        return f"target {self.index + 1}/{self.total} above leaf {leaf}"


def resolve_sync_paths(
    genesis_hash: Hash, fixture: BlockchainEngineXFixture
) -> list[SyncPath]:
    """
    Return the served path behind each of the fixture's sync targets.

    A fixture without targets - a chain asserting an Engine API error
    code, one whose leaves admit no child block, one that opted out
    (`sync_block=False`), or a fill with `--no-sync-block` - yields one
    path: the authored payloads exactly as written, announced by their
    own head.

    For each target the authored ancestry is resolved by hash: start
    from the target's `parentHash`, look up that authored payload, and
    follow `parentHash` links backwards until `genesis_hash`. A parent
    that is neither genesis nor an authored payload, a duplicate
    authored block hash, a cycle, or a target sitting directly above
    genesis raises `SyncTargetResolutionError` naming the target - a
    corpus defect, not a skip.
    """
    targets = fixture.sync_payloads
    if not targets:
        return [
            SyncPath(
                index=0,
                total=1,
                target=fixture.payloads[-1],
                authored=tuple(fixture.payloads),
                announces_scaffolding=False,
            )
        ]

    payloads_by_hash: dict[Hash, FixtureEngineNewPayload] = {}
    for payload in fixture.payloads:
        block_hash = _block_hash(payload)
        if block_hash in payloads_by_hash:
            raise SyncTargetResolutionError(
                f"two authored payloads declare block hash {block_hash}; "
                "hash-based ancestry cannot tell them apart"
            )
        payloads_by_hash[block_hash] = payload

    paths: list[SyncPath] = []
    total = len(targets)
    for index, target in enumerate(targets):
        name = f"sync target {index + 1}/{total}"
        authored: list[FixtureEngineNewPayload] = []
        visited: set[Hash] = set()
        current = _parent_hash(target)
        while current != genesis_hash:
            if current in visited:
                raise SyncTargetResolutionError(
                    f"{name}'s authored ancestry cycles at {current}"
                )
            visited.add(current)
            payload = payloads_by_hash.get(current)
            if payload is None:
                raise SyncTargetResolutionError(
                    f"{name} descends from {current}, which is neither "
                    "genesis nor an authored payload"
                )
            authored.append(payload)
            current = _parent_hash(payload)
        if not authored:
            raise SyncTargetResolutionError(
                f"{name} sits directly above genesis and selects no "
                "authored payload"
            )
        authored.reverse()
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


def _path_lengths_from_links(
    parent_by_hash: dict[Hash, Hash] | dict[str, str],
    target_parents: list[Hash] | list[str],
) -> list[int]:
    """
    Return each target's served-chain length from parent links alone.

    Used at collection time, where the pre-allocation group's genesis
    hash is not available: the walk simply stops at the first hash
    that is not an authored payload, which for a well-formed fixture
    is genesis. Anomalies (a cycle, a dangling parent) end the walk
    rather than raise - collection must not fail for a defect the
    test itself will diagnose properly - so the returned length is a
    lower bound in that case.
    """
    lengths: list[int] = []
    for parent in target_parents:
        depth = 0
        visited = set()
        current = parent
        while current in parent_by_hash and current not in visited:
            visited.add(current)
            depth += 1
            current = parent_by_hash[current]  # type: ignore[index]
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


def raw_target_path_lengths(raw_fixture: dict) -> list[int]:
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
