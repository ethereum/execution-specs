"""Pre-allocation group models for test fixture generation."""

import json
import os
from dataclasses import dataclass
from hashlib import sha256
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
    Tuple,
)

from pydantic import Field, PrivateAttr

from execution_testing.base_types import (
    CamelModel,
    EthereumTestRootModel,
    Hash,
    ZeroPaddedHexNumber,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.test_types import Alloc, AllocGroupHash, Environment
from execution_testing.test_types.chain_config_types import DEFAULT_CHAIN_ID

from .blockchain import FixtureHeader


class PreAllocGroupCommon(CamelModel):
    """
    Fields that identify a pre-allocation group, in either of its two forms.

    `PreAllocGroupBuilder` is the scratch accumulator phase 1 fills in and
    must never publish; `PreAllocGroup` is the artifact consumers read. The
    two are not interchangeable and share only the fields below.
    """

    test_ids: List[str] = Field(default_factory=list)
    fork: Fork | TransitionFork = Field(..., alias="network")
    chain_id: ZeroPaddedHexNumber = ZeroPaddedHexNumber(DEFAULT_CHAIN_ID)
    group_salt: str | None = Field(
        None,
        description=(
            "Explicit isolation salt from the `pre_alloc_group` marker; "
            "groups only pack with groups carrying the same salt."
        ),
    )
    group_hash: AllocGroupHash | None = None

    @classmethod
    def from_file(cls, file: Path) -> Self:
        """
        Load a pre-allocation group or builder from a JSON file.

        Additionally, verify that the file name contains the group hash.
        """
        instance = cls.model_validate_json(file.read_bytes())
        if str(instance.group_hash).lower() not in file.stem.lower():
            raise Exception(
                f"Pre-alloc group file name `{file}` does not contain the "
                "group hash contained in the file "
                f"`{str(instance.group_hash)}`"
            )
        return instance


class PreAllocGroupBuilder(PreAllocGroupCommon):
    """
    Pre-allocation group temporary builder.

    This file must _NOT_ be saved as the final output of the filling process.
    """

    environment: Environment = Field(
        ..., description="Grouping environment for this test group"
    )
    pre: Alloc

    def model_post_init(self, __context: Any) -> None:
        """
        Seed the pre-alloc's commitment scheme from its genesis fork.
        """
        super().model_post_init(__context)
        self.pre.migrate_state_commitment(
            self.fork.transitions_from().state_commitment()
        )

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
        assert self.pre.state_commitment() == new_pre.state_commitment()
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
            fork=self.fork,
            chain_id=self.chain_id,
            group_salt=self.group_salt,
            group_hash=self.group_hash,
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
        computed once when the `build` method is used to construct the final
        `PreAllocGroup`.
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
                merged_builder.build().model_dump_json(
                    by_alias=True, exclude_none=True, indent=2
                )
            )


class PreAllocGroupBuilders(EthereumTestRootModel):
    """Root model mapping pre-allocation group builders to group hashes."""

    root: Dict[AllocGroupHash, PreAllocGroupBuilder] = Field(
        default_factory=dict
    )

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
        pre_alloc_hash: AllocGroupHash,
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
                group_hash=pre_alloc_hash,
                # Plain `Alloc` copy, so later tests can be merged into it.
                pre=Alloc(pre.root),
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
    _pre_alloc_group_hash: AllocGroupHash | None = PrivateAttr(None)
    _genesis_accounts: Literal["absent", "seeded", "deferred"] = PrivateAttr(
        "seeded"
    )
    """Built from the seeded `pre` of every test in the group."""

    def structural_copy(self) -> Self:
        """
        Return a copy to execute blocks against, without the cached state
        root and model dump, which describe the group's genesis rather than
        the copy.
        """
        copied = super().structural_copy()
        copied._cached_state_root = None
        copied._model_dump_cache = None
        return copied

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

    def get_alloc_grouping_hash(self) -> AllocGroupHash | None:
        """
        Return the grouping hash if the allocation belongs to a particular
        group, otherwise `None`.

        Method can be overloaded by other implementations of the Alloc to
        return the appropriate group.
        """
        return self._pre_alloc_group_hash


class PreAllocGroup(PreAllocGroupCommon):
    """
    Pre-allocation group for tests with identical Environment and fork values.

    Grouping is still keyed on the tests' fixture Environment and fork, but
    that Environment lives in phase 1 (`PreAllocGroupBuilder`) only: what
    reaches the final group is the `genesis` header derived from it.
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
        self.pre._pre_alloc_group_hash = self.group_hash

    def hash(self) -> Hash:
        """
        Return a Hash based on the canonical JSON of the model.
        """
        canonical_json = json.dumps(
            self.model_dump(mode="json", by_alias=True, exclude_none=True),
            sort_keys=True,
        )
        return Hash(sha256(canonical_json.encode("utf-8")).digest())


class PreAllocGroups(EthereumTestRootModel):
    """
    Root model mapping pre-allocation group hashes to test groups.

    If lazy_load is True, the groups are not loaded from the folder until they
    are accessed.

    Iterating will fail if lazy_load is True.
    """

    root: Dict[AllocGroupHash, PreAllocGroup | None] = Field(
        default_factory=dict
    )

    _folder_source: Path | None = PrivateAttr(None)

    def __setitem__(self, key: AllocGroupHash, value: Any) -> None:
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

        data: Dict[AllocGroupHash, PreAllocGroup | None] = {}
        for file in folder.glob("*.json"):
            if lazy_load:
                data[AllocGroupHash(file.stem)] = None
            else:
                data[AllocGroupHash(file.stem)] = PreAllocGroup.from_file(file)
        instance = cls(root=data)
        if lazy_load:
            instance._folder_source = folder
        return instance

    def __getitem__(self, item: AllocGroupHash) -> PreAllocGroup:
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

    def __iter__(self) -> Iterator[AllocGroupHash]:  # type: ignore [override]
        """Iterate over root dict."""
        return iter(self.root)

    def __contains__(self, item: AllocGroupHash) -> bool:
        """Check if item in root dict."""
        return item in self.root

    def __len__(self) -> int:
        """Get length of root dict."""
        return len(self.root)

    def keys(self) -> KeysView[AllocGroupHash]:
        """Get keys from root dict."""
        return self.root.keys()

    def values(self) -> Generator[PreAllocGroup, None, None]:
        """Get values from root dict."""
        for value in self.root.values():
            assert value is not None, "Value is None"
            yield value

    def items(
        self,
    ) -> Generator[Tuple[AllocGroupHash, PreAllocGroup], None, None]:
        """Get items from root dict."""
        for key, value in self.root.items():
            assert value is not None, f"Value for key {key} is None"
            yield key, value
