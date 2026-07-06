"""Pre-allocation group models for test fixture generation."""

import hashlib
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generator,
    Iterator,
    KeysView,
    List,
    Literal,
    Optional,
    Self,
    Set,
    Tuple,
)

from pydantic import Field, PrivateAttr

from execution_testing.base_types import (
    CamelModel,
    EthereumTestRootModel,
    Hash,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.test_types import Alloc, Environment
from execution_testing.test_types.chain_config_types import DEFAULT_CHAIN_ID

from .blockchain import FixtureHeader


class PreAllocGroupBuilder(CamelModel):
    """Pre-allocation group builder."""

    test_ids: List[str] = Field(default_factory=list)
    environment: Environment = Field(
        ..., description="Grouping environment for this test group"
    )
    fork: Fork | TransitionFork = Field(..., alias="network")
    chain_id: int = DEFAULT_CHAIN_ID
    group_salt: str | None = Field(
        None,
        description=(
            "Explicit isolation salt from the `pre_alloc_group` marker; "
            "groups only pack with groups carrying the same salt."
        ),
    )
    pre: Alloc

    def get_pre_account_count(self) -> int:
        """Return the amount of accounts the pre-allocation group holds."""
        return len(self.pre.root)

    def get_test_count(self) -> int:
        """Return the amount of tests that use this pre-allocation group."""
        return len(self.test_ids)

    def calculate_genesis(self) -> FixtureHeader:
        """Get the genesis header for this group."""
        return FixtureHeader.genesis(
            self.fork.transitions_from(),
            self.environment,
            self.pre.state_root(),
        )

    def add_test_alloc(self, test_id: str, new_pre: Alloc) -> None:
        """Adds a pre to this builder's pre."""
        self.pre = Alloc.merge(
            self.pre,
            new_pre,
            key_collision_mode=Alloc.KeyCollisionMode.ALLOW_IDENTICAL_ACCOUNTS,
        )
        self.test_ids.append(test_id)

    def build(self) -> "PreAllocGroup":
        """Build the pre-alloc group."""
        return PreAllocGroup(
            test_ids=self.test_ids,
            environment=self.environment,
            fork=self.fork,
            chain_id=self.chain_id,
            group_salt=self.group_salt,
            pre=self.pre.model_dump(),
            pre_account_count=self.get_pre_account_count(),
            test_count=self.get_test_count(),
            genesis=self.calculate_genesis(),
        )

    def to_partial_file(
        self, file: Path, worker_id: Optional[str] = None
    ) -> None:
        """
        Save PreAllocGroupBuilder to a partial file (no locking).

        Each worker writes its own partial file, which are merged at session
        end by merge_partial_group_files(). This eliminates lock contention
        that caused workers to take 30-180+ seconds each.

        Saves the builder format (without genesis/state_root) to avoid
        expensive state root computation during Phase 1. State root is
        computed once when loading in Phase 2 via PreAllocGroup.from_file().
        """
        suffix = f".{worker_id}" if worker_id else ".main"
        partial_path = file.with_suffix(f".partial{suffix}.json")
        partial_path.write_text(
            self.model_dump_json(by_alias=True, exclude_none=True, indent=2)
        )


def _get_worker_id() -> Optional[str]:
    """Get the xdist worker ID from environment, or None if not in xdist."""
    return os.environ.get("PYTEST_XDIST_WORKER")


def merge_partial_group_files(folder: Path) -> None:
    """
    Merge all partial group files into final group files.

    Called by master process after all workers have finished Phase 1.
    Each worker writes {group_hash}.partial.{worker_id}.json files,
    which are merged here into {group_hash}.json files.
    """
    partial_files = list(folder.glob("*.partial.*.json"))
    if not partial_files:
        return

    # Group partials by target: {hash}.partial.{worker}.json -> {hash}.json
    partials_by_target: Dict[Path, List[Path]] = {}
    for partial in partial_files:
        name = partial.name
        idx = name.find(".partial.")
        if idx == -1:
            continue
        target_name = name[:idx] + ".json"
        target_path = partial.parent / target_name
        if target_path not in partials_by_target:
            partials_by_target[target_path] = []
        partials_by_target[target_path].append(partial)

    # Merge each group's partials
    for target_path, partials in partials_by_target.items():
        merged_builder: Optional[PreAllocGroupBuilder] = None

        for partial in partials:
            builder = PreAllocGroupBuilder.model_validate_json(
                partial.read_text()
            )

            if merged_builder is None:
                merged_builder = builder
            else:
                # Merge pre-allocations (check for collisions)
                for account in builder.pre:
                    new_account = builder.pre[account]
                    if account not in merged_builder.pre:
                        merged_builder.pre[account] = new_account
                    else:
                        existing_account = merged_builder.pre[account]
                        if new_account != existing_account:
                            # Write collision file for error reporting
                            collision_file_path = target_path.with_suffix(
                                ".fail"
                            )
                            collision_exception = Alloc.CollisionError(
                                address=account,
                                account_1=existing_account,
                                account_2=new_account,
                            )
                            collision_file_path.write_text(
                                json.dumps(collision_exception.to_json())
                            )
                            raise collision_exception

                # Merge test_ids
                merged_builder.test_ids.extend(builder.test_ids)

            # Clean up partial file after processing
            partial.unlink()

        # Write final merged file
        if merged_builder is not None:
            target_path.write_text(
                merged_builder.model_dump_json(
                    by_alias=True, exclude_none=True, indent=2
                )
            )


def _environment_group_key(environment: Environment) -> str:
    """
    Return a stable string identifying a genesis environment.

    Two groups can only share a client if they share a genesis block, so the
    environment is part of every packing bucket. The canonical JSON dump
    matches the equality semantics of `Environment` (which compares the
    alias-keyed, none-excluded dump).
    """
    return json.dumps(
        environment.model_dump(mode="json", by_alias=True, exclude_none=True),
        sort_keys=True,
    )


def _packed_group_hash(test_ids: List[str]) -> str:
    """Return a deterministic ``0x``-prefixed id for a packed group."""
    digest = hashlib.sha256("\n".join(test_ids).encode("utf-8")).digest()
    return f"0x{int.from_bytes(digest[:8], byteorder='big'):016x}"


# The test id -> group hash index written next to the group files by
# `pack_pre_alloc_groups`. Deliberately not a `*.json` name: every consumer
# of the folder (including this module) discovers group files by that glob.
TEST_GROUP_INDEX_FILE = "test_group_index"


def read_test_group_index(folder: Path) -> Dict[str, str]:
    """
    Map every test id to the hash of the pre-alloc group that contains it.

    Prefer the index file written by `pack_pre_alloc_groups`; fall back to
    scanning every group file's ``testIds`` for folders produced without a
    packing pass (e.g. by an older framework version).
    """
    index_file = folder / TEST_GROUP_INDEX_FILE
    if index_file.exists():
        return json.loads(index_file.read_text())
    index: Dict[str, str] = {}
    for file in folder.glob("*.json"):
        data = json.loads(file.read_text())
        for test_id in data.get("testIds", []):
            index[test_id] = file.stem
    return index


# Addresses below this value are precompiles / the reserved range. A ported
# state test can call them without ever declaring them in its pre, so an
# account introduced there by another test in the group silently changes its
# execution.
_RESERVED_ADDRESS_CEILING = 0x100


def _reserved_addresses(builders: List["PreAllocGroupBuilder"]) -> Set[str]:
    """
    Return the addresses that are unsafe to introduce via a merge.

    A shared genesis leaks every account it holds to every test in the group.
    A ported state test only declares the accounts it sets and assumes all
    other addresses are empty, so introducing an account at an address it
    quietly depends on (a precompile, a canonical scratch contract, ...)
    changes its result. Two kinds of address are therefore reserved: the low
    precompile range, and any address more than one group allocates (i.e. a
    shared/canonical address rather than one private to a single test).
    """
    frequency: Dict[str, int] = defaultdict(int)
    for builder in builders:
        for address in builder.pre.root:
            frequency[str(address)] += 1
    return {
        address
        for address, count in frequency.items()
        if count > 1 or int(address, 16) < _RESERVED_ADDRESS_CEILING
    }


def _reserved_signature(
    builder: "PreAllocGroupBuilder", reserved: Set[str]
) -> Tuple[Tuple[str, str], ...]:
    """
    Return a group's reserved-address footprint as a hashable signature.

    Groups may only merge when this matches exactly, so every test in a packed
    group sees identical reserved accounts (and identically absent ones).
    """
    return tuple(
        sorted(
            (
                str(address),
                "null"
                if account is None
                else json.dumps(
                    account.model_dump(mode="json"), sort_keys=True
                ),
            )
            for address, account in builder.pre.root.items()
            if str(address) in reserved
        )
    )


def pack_pre_alloc_groups(folder: Path) -> None:
    """
    Merge fine-grained pre-allocation groups into fewer, larger ones.

    Phase 1 keys every test's group on the exact content of any hard-coded
    accounts it sets (`modified_accounts_salt`), so a test that pins accounts
    to fixed addresses lands in its own group even when it could safely share a
    genesis with others. This is conservative: it splits far more than the
    genuine address conflicts require. `groupstats` shows this dominates the
    group count, with most groups a single test.

    This pass reclaims that while preserving each test's isolation. Groups
    are bucketed by everything a shared genesis requires (fork, chain id, and
    environment), by the explicit `pre_alloc_group` marker salt (so a test
    that demands its own genesis keeps it), and then by their
    reserved-address footprint (see `_reserved_addresses`), so two tests only
    share a genesis when they agree on every precompile and shared address.
    Within a bucket the reserved accounts are identical and the remaining
    (test-private) addresses are unique to one group, so the union is always
    conflict-free and the whole bucket collapses to a single group.

    The packing is deterministic: buckets are processed in sorted order and
    each group's id is derived from its sorted test ids, so a re-fill of the
    same tests reproduces the same groups.

    Called on the master process after `merge_partial_group_files`, replacing
    the fine-grained files in `folder` with the packed ones. Also writes a
    test id -> group hash index file (see `read_test_group_index`), so phase
    2 workers can find a test's group without scanning every group file.
    """
    files = sorted(folder.glob("*.json"))
    if not files:
        return

    builders = [
        PreAllocGroupBuilder.model_validate_json(file.read_text())
        for file in files
    ]

    genesis_buckets: Dict[
        Tuple[str, int, str, str], List[PreAllocGroupBuilder]
    ] = defaultdict(list)
    for builder in builders:
        genesis_buckets[
            (
                builder.fork.name(),
                builder.chain_id,
                builder.group_salt or "",
                _environment_group_key(builder.environment),
            )
        ].append(builder)

    # Drop the fine-grained files up front; the packed files written below are
    # named by content hash and never clash with the (now stale) originals.
    for file in files:
        file.unlink()

    test_group_index: Dict[str, str] = {}
    for genesis_key in sorted(genesis_buckets):
        bucket = genesis_buckets[genesis_key]
        reserved = _reserved_addresses(bucket)

        packed: Dict[Tuple[Tuple[str, str], ...], PreAllocGroupBuilder] = {}
        for builder in bucket:
            signature = _reserved_signature(builder, reserved)
            if signature in packed:
                merged = packed[signature]
                merged.pre.root.update(builder.pre.root)
                merged.test_ids.extend(builder.test_ids)
            else:
                packed[signature] = builder

        for merged in packed.values():
            merged.test_ids.sort()
            packed_hash = _packed_group_hash(merged.test_ids)
            (folder / f"{packed_hash}.json").write_text(
                merged.model_dump_json(
                    by_alias=True, exclude_none=True, indent=2
                )
            )
            for test_id in merged.test_ids:
                test_group_index[test_id] = packed_hash

    (folder / TEST_GROUP_INDEX_FILE).write_text(
        json.dumps(test_group_index, sort_keys=True, indent=2)
    )


class PreAllocGroupBuilders(EthereumTestRootModel):
    """
    Root model mapping pre-allocation group hashes to test groups.

    If lazy_load is True, the groups are not loaded from the folder until they
    are accessed.

    Iterating will fail if lazy_load is True.
    """

    root: Dict[str, PreAllocGroupBuilder]

    def to_folder(self, folder: Path, worker_id: Optional[str] = None) -> None:
        """
        Save PreAllocGroups to a folder as partial files.

        Each worker writes its own partial files (no lock contention).
        Call merge_partial_group_files() on master after all workers finish.
        """
        for key, value in self.root.items():
            assert value is not None, f"Value for key {key} is None"
            value.to_partial_file(folder / f"{key}.json", worker_id=worker_id)

    def add_test_pre(
        self,
        *,
        pre_alloc_hash: str,
        test_id: str,
        fork: Fork | TransitionFork,
        chain_id: int,
        environment: Environment,
        pre: Alloc,
        group_salt: str | None = None,
    ) -> None:
        """Adds a single test to the appropriate group based on the hash."""
        if pre_alloc_hash in self.root:
            # Update existing group - just merge pre-allocations
            group = self.root[pre_alloc_hash]
            assert group.fork == fork, (
                f"Incompatible fork: {group.fork}!={fork}"
            )
            assert group.chain_id == chain_id, (
                f"Incompatible chain id: {group.chain_id}!={chain_id}"
            )
            assert group.group_salt == group_salt, (
                f"Incompatible group salt: {group.group_salt}!={group_salt}"
            )
            group.add_test_alloc(test_id, pre)
        else:
            # Create new group - use Environment instead of expensive genesis
            # generation
            group = PreAllocGroupBuilder(
                test_ids=[test_id],
                fork=fork,
                chain_id=chain_id,
                environment=environment,
                group_salt=group_salt,
                pre=Alloc.merge(
                    Alloc.model_validate(
                        fork.transitions_to().pre_allocation_blockchain()
                    ),
                    pre,
                ),
            )
            self.root[pre_alloc_hash] = group


@dataclass(kw_only=True)
class ModelDumpCache:
    """
    Holds a cached dump of a model, the type of the cache (str or json)
    and the keyword arguments used to generate it.
    """

    model_dump_config: Dict[str, Any]
    """Keyword arguments used to model dump the data."""
    model_dump_mode: Literal["json", "python"]
    """Mode of the model dump when `model_dump` is called."""
    model_dump_type: Literal["string", "dict"]
    """Whether `model_dump_json` or `model_dump` was used to generate data."""
    data: Any


class GroupPreAlloc(Alloc):
    """
    Alloc that belongs to a pre-allocation group.

    This is used to avoid re-calculating the state root for the pre-allocation
    group when it is accessed.

    Also holds a cached model dump of the pre-allocation group, either in
    string or JSON format depending on the last request.
    """

    _cached_state_root: Hash | None = PrivateAttr(None)
    _model_dump_cache: ModelDumpCache | None = PrivateAttr(None)

    def state_root(self) -> Hash:
        """On pre-alloc groups, which are normally very big, always cache."""
        if self._cached_state_root is not None:
            return self._cached_state_root
        return super().state_root()

    def model_dump(  # type: ignore[override]
        self, mode: Literal["json", "python"], **kwargs: Any
    ) -> Any:
        """
        Model dump the pre-allocation group, with caching.

        Note: 'mode' here follows Pydantic's semantics:
        - 'python' -> standard model_dump
        - 'json'   -> JSON-compatible python data
        """
        if (
            self._model_dump_cache is not None
            and self._model_dump_cache.model_dump_mode == mode
            and self._model_dump_cache.model_dump_type == "dict"
            and self._model_dump_cache.model_dump_config == kwargs
        ):
            return self._model_dump_cache.data

        data = super().model_dump(mode=mode, **kwargs)
        self._model_dump_cache = ModelDumpCache(
            model_dump_mode=mode,
            model_dump_config=kwargs,
            model_dump_type="dict",
            data=data,
        )
        return data

    def model_dump_json(self, **kwargs: Any) -> str:
        """Model dump the pre-allocation group in JSON string, with caching."""
        if (
            self._model_dump_cache is not None
            and self._model_dump_cache.model_dump_mode == "json"
            and self._model_dump_cache.model_dump_type == "string"
            and self._model_dump_cache.model_dump_config == kwargs
        ):
            return self._model_dump_cache.data

        data = super().model_dump_json(**kwargs)
        self._model_dump_cache = ModelDumpCache(
            model_dump_mode="json",
            model_dump_config=kwargs,
            model_dump_type="string",
            data=data,
        )
        return data


class PreAllocGroup(PreAllocGroupBuilder):
    """
    Pre-allocation group for tests with identical Environment and fork values.

    Groups tests by a hash of their fixture Environment and fork to enable
    pre-allocation group optimization.
    """

    pre: GroupPreAlloc
    genesis: FixtureHeader
    pre_account_count: int
    test_count: int

    def model_post_init(self, __context: Any) -> None:
        """
        Model post init method to cache the state root in GroupPreAlloc.
        """
        super().model_post_init(__context)
        self.pre._cached_state_root = self.genesis.state_root

    @classmethod
    def from_file(cls, file: Path) -> Self:
        """
        Load a pre-allocation group from a JSON file.

        Files are stored in builder format (without genesis). Genesis is
        computed on-demand when loading, ensuring state root computation
        happens exactly once in Phase 2, not during Phase 1 merging.
        """
        with open(file) as f:
            data = f.read()

        builder = PreAllocGroupBuilder.model_validate_json(data)
        built = builder.build()
        # Use cls.model_validate to ensure proper Self return type
        return cls.model_validate(built.model_dump())


class PreAllocGroups(EthereumTestRootModel):
    """
    Root model mapping pre-allocation group hashes to test groups.

    If lazy_load is True, the groups are not loaded from the folder until they
    are accessed.

    Iterating will fail if lazy_load is True.
    """

    root: Dict[str, PreAllocGroup | None]

    _folder_source: Path | None = PrivateAttr(None)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set item in root dict."""
        assert self._folder_source is None, (
            "Cannot set item in root dict after folder source is set"
        )
        self.root[key] = value

    @classmethod
    def from_folder(cls, folder: Path, *, lazy_load: bool = False) -> Self:
        """Create PreAllocGroups from a folder of pre-allocation files."""
        # First check for collision failures
        for fail_file in folder.glob("*.fail"):
            with open(fail_file) as f:
                raise Alloc.CollisionError.from_json(json.loads(f.read()))

        data: Dict[str, PreAllocGroup | None] = {}
        for file in folder.glob("*.json"):
            if lazy_load:
                data[file.stem] = None
            else:
                data[file.stem] = PreAllocGroup.from_file(file)
        instance = cls(root=data)
        if lazy_load:
            instance._folder_source = folder
        return instance

    def __getitem__(self, item: str) -> PreAllocGroup:
        """Get item from root dict."""
        if self._folder_source is None:
            value = self.root[item]
            assert value is not None, f"Item {item} is None"
            return value
        else:
            if self.root[item] is None:
                self.root[item] = PreAllocGroup.from_file(
                    self._folder_source / f"{item}.json"
                )
            result = self.root[item]
            assert result is not None
            return result

    def __iter__(self) -> Iterator[str]:  # type: ignore [override]
        """Iterate over root dict."""
        return iter(self.root)

    def __contains__(self, item: str) -> bool:
        """Check if item in root dict."""
        return item in self.root

    def __len__(self) -> int:
        """Get length of root dict."""
        return len(self.root)

    def keys(self) -> KeysView[str]:
        """Get keys from root dict."""
        return self.root.keys()

    def values(self) -> Generator[PreAllocGroup, None, None]:
        """Get values from root dict."""
        for value in self.root.values():
            assert value is not None, "Value is None"
            yield value

    def items(self) -> Generator[Tuple[str, PreAllocGroup], None, None]:
        """Get items from root dict."""
        for key, value in self.root.items():
            assert value is not None, f"Value for key {key} is None"
            yield key, value
