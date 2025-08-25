"""Pre-allocation group models for test fixture generation."""

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

from filelock import FileLock
from pydantic import Field, PrivateAttr, computed_field

from ethereum_test_base_types import CamelModel, EthereumTestRootModel
from ethereum_test_forks import Fork
from ethereum_test_types import Alloc, Environment

from .blockchain import FixtureHeader


class PreAllocGroup(CamelModel):
    """
    Pre-allocation group for tests with identical Environment and fork values.

    Groups tests by a hash of their fixture Environment and fork to enable
    pre-allocation group optimization.
    """

    model_config = {"populate_by_name": True}  # Allow both field names and aliases

    test_ids: List[str] = Field(default_factory=list)
    environment: Environment = Field(..., description="Grouping environment for this test group")
    fork: Fork = Field(..., alias="network")
    pre: Alloc

    @computed_field(description="Number of accounts in the pre-allocation")  # type: ignore[prop-decorator]
    @property
    def pre_account_count(self) -> int:
        """Return the amount of accounts the pre-allocation group holds."""
        return len(self.pre.root)

    @computed_field(description="Number of tests in this group")  # type: ignore[prop-decorator]
    @property
    def test_count(self) -> int:
        """Return the amount of tests that use this pre-allocation group."""
        return len(self.test_ids)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def genesis(self) -> FixtureHeader:
        """Get the genesis header for this group."""
        return FixtureHeader.genesis(
            self.fork,
            self.environment,
            self.pre.state_root(),
        )

    def to_file(self, file: Path) -> None:
        """Save PreAllocGroup to a file."""
        lock_file_path = file.with_suffix(".lock")
        with FileLock(lock_file_path):
            if file.exists():
                with open(file, "r") as f:
                    previous_pre_alloc_group = PreAllocGroup.model_validate_json(f.read())
                for account in previous_pre_alloc_group.pre:
                    existing_account = previous_pre_alloc_group.pre[account]
                    if account not in self.pre:
                        self.pre[account] = existing_account
                    else:
                        new_account = self.pre[account]
                        if new_account != existing_account:
                            # This procedure fails during xdist worker's pytest_sessionfinish
                            # and is not reported to the master thread.
                            # We signal here that the groups created contain a collision.
                            collision_file_path = file.with_suffix(".fail")
                            collision_exception = Alloc.CollisionError(
                                address=account,
                                account_1=existing_account,
                                account_2=new_account,
                            )
                            with open(collision_file_path, "w") as f:
                                f.write(json.dumps(collision_exception.to_json()))
                            raise collision_exception
                self.test_ids.extend(previous_pre_alloc_group.test_ids)

            with open(file, "w") as f:
                f.write(self.model_dump_json(by_alias=True, exclude_none=True, indent=2))


class PreAllocGroups(EthereumTestRootModel):
    """
    Root model mapping pre-allocation group hashes to test groups.

    If lazy_load is True, the groups are not loaded from the folder until they are accessed.

    Iterating will fail if lazy_load is True.
    """

    root: Dict[str, PreAllocGroup | None]

    _folder_source: Path | None = PrivateAttr(None)

    def __setitem__(self, key: str, value: Any):
        """Set item in root dict."""
        assert self._folder_source is None, (
            "Cannot set item in root dict after folder source is set"
        )
        self.root[key] = value

    @classmethod
    def from_folder(cls, folder: Path, *, lazy_load: bool = False) -> "PreAllocGroups":
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
                with open(file) as f:
                    data[file.stem] = PreAllocGroup.model_validate_json(f.read())
        instance = cls(root=data)
        if lazy_load:
            instance._folder_source = folder
        return instance

    def to_folder(self, folder: Path) -> None:
        """Save PreAllocGroups to a folder of pre-allocation files."""
        for key, value in self.root.items():
            assert value is not None, f"Value for key {key} is None"
            value.to_file(folder / f"{key}.json")

    def __getitem__(self, item):
        """Get item from root dict."""
        if self._folder_source is None:
            item = self.root[item]
            assert item is not None, f"Item {item} is None"
            return item
        else:
            if self.root[item] is None:
                with open(self._folder_source / f"{item}.json") as f:
                    self.root[item] = PreAllocGroup.model_validate_json(f.read())
            return self.root[item]

    def __iter__(self):
        """Iterate over root dict."""
        return iter(self.root)

    def __contains__(self, item):
        """Check if item in root dict."""
        return item in self.root

    def __len__(self):
        """Get length of root dict."""
        return len(self.root)

    def keys(self):
        """Get keys from root dict."""
        return self.root.keys()

    def values(self) -> Iterator[PreAllocGroup]:
        """Get values from root dict."""
        for value in self.root.values():
            assert value is not None, "Value is None"
            yield value

    def items(self) -> Iterator[Tuple[str, PreAllocGroup]]:
        """Get items from root dict."""
        for key, value in self.root.items():
            assert value is not None, f"Value for key {key} is None"
            yield key, value
