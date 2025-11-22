"""Pre-allocation group models for test fixture generation."""

import json
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, KeysView, List, Self, Tuple

from filelock import FileLock
from pydantic import Field, PrivateAttr

from execution_testing.base_types import (
    CamelModel,
    EthereumTestRootModel,
    Hash,
)
from execution_testing.forks import Fork
from execution_testing.test_types import Alloc, Environment

from .blockchain import FixtureHeader


class PreAllocGroupBuilder(CamelModel):
    """Pre-allocation group builder."""

    test_ids: List[str] = Field(default_factory=list)
    environment: Environment = Field(
        ..., description="Grouping environment for this test group"
    )
    fork: Fork = Field(..., alias="network")
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
            self.fork,
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
            pre=self.pre.model_dump(),
            pre_account_count=self.get_pre_account_count(),
            test_count=self.get_test_count(),
            genesis=self.calculate_genesis(),
        )

    def to_file(self, file: Path) -> None:
        """Save PreAllocGroup to a file."""
        lock_file_path = file.with_suffix(".lock")
        with FileLock(lock_file_path):
            if file.exists():
                with open(file, "r") as f:
                    previous_pre_alloc_group = (
                        PreAllocGroup.model_validate_json(f.read())
                    )
                for account in previous_pre_alloc_group.pre:
                    existing_account = previous_pre_alloc_group.pre[account]
                    if account not in self.pre:
                        self.pre[account] = existing_account
                    else:
                        new_account = self.pre[account]
                        if new_account != existing_account:
                            # This procedure fails during xdist worker's
                            # pytest_sessionfinish and is not reported to the
                            # master thread. We signal here that the groups
                            # created contain a collision.
                            collision_file_path = file.with_suffix(".fail")
                            collision_exception = Alloc.CollisionError(
                                address=account,
                                account_1=existing_account,
                                account_2=new_account,
                            )
                            with open(collision_file_path, "w") as f:
                                f.write(
                                    json.dumps(collision_exception.to_json())
                                )
                            raise collision_exception
                self.test_ids.extend(previous_pre_alloc_group.test_ids)
            with open(file, "w") as f:
                f.write(
                    self.build().model_dump_json(
                        by_alias=True, exclude_none=True, indent=2
                    )
                )


class PreAllocGroupBuilders(EthereumTestRootModel):
    """
    Root model mapping pre-allocation group hashes to test groups.

    If lazy_load is True, the groups are not loaded from the folder until they
    are accessed.

    Iterating will fail if lazy_load is True.
    """

    root: Dict[str, PreAllocGroupBuilder]

    def to_folder(self, folder: Path) -> None:
        """Save PreAllocGroups to a folder of pre-allocation files."""
        for key, value in self.root.items():
            assert value is not None, f"Value for key {key} is None"
            value.to_file(folder / f"{key}.json")

    def add_test_pre(
        self,
        *,
        pre_alloc_hash: str,
        test_id: str,
        fork: Fork,
        environment: Environment,
        pre: Alloc,
    ) -> None:
        """Adds a single test to the appropriate group based on the hash."""
        if pre_alloc_hash in self.root:
            # Update existing group - just merge pre-allocations
            group = self.root[pre_alloc_hash]
            assert group.fork == fork, (
                f"Incompatible fork: {group.fork}!={fork}"
            )
            group.add_test_alloc(test_id, pre)
        else:
            # Create new group - use Environment instead of expensive genesis
            # generation
            group = PreAllocGroupBuilder(
                test_ids=[test_id],
                fork=fork,
                environment=environment,
                pre=Alloc.merge(
                    Alloc.model_validate(fork.pre_allocation_blockchain()),
                    pre,
                ),
            )
            self.root[pre_alloc_hash] = group


class GroupPreAlloc(Alloc):
    _pre_alloc_group: "PreAllocGroup" = PrivateAttr(init=False)

    def state_root(self) -> Hash:
        """On pre-alloc groups, which are normally very big, we always cache."""
        return self._pre_alloc_group.genesis.state_root


class PreAllocGroup(PreAllocGroupBuilder):
    """
    Pre-allocation group for tests with identical Environment and fork values.

    Groups tests by a hash of their fixture Environment and fork to enable
    pre-allocation group optimization.
    """

    # Allow both field names and aliases
    model_config = {"populate_by_name": True}
    pre: GroupPreAlloc
    genesis: FixtureHeader
    pre_account_count: int
    test_count: int

    def model_post_init(self, __context: Any) -> None:
        """
        Model post init method to set GroupPreAlloc reference.
        """
        super().model_post_init(__context)
        self.pre._pre_alloc_group = self

    @classmethod
    def from_file(cls, file: Path) -> Self:
        """Load a pre-allocation group from a JSON file."""
        with open(file) as f:
            return cls.model_validate_json(f.read())


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
