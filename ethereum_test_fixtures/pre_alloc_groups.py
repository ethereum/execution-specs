"""Pre-allocation group models for test fixture generation."""

from pathlib import Path
from typing import Any, Dict, List

from filelock import FileLock
from pydantic import Field, computed_field

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

    test_count: int = Field(0, description="Number of tests in this group")
    pre_account_count: int = Field(0, description="Number of accounts in the pre-allocation")
    test_ids: List[str] = Field(default_factory=list, alias="testIds")
    environment: Environment = Field(..., description="Grouping environment for this test group")
    fork: Fork = Field(..., alias="network")
    pre: Alloc

    def model_post_init(self, __context):
        """Post-init hook to ensure pre is not None."""
        super().model_post_init(__context)

        self.pre = Alloc.merge(
            Alloc.model_validate(self.fork.pre_allocation_blockchain()),
            self.pre,
        )

    @computed_field  # type: ignore[misc]
    def genesis(self) -> FixtureHeader:
        """Get the genesis header for this group."""
        return FixtureHeader.genesis(
            self.fork,
            self.environment.set_fork_requirements(self.fork),
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
                        if account not in self.pre:
                            self.pre[account] = previous_pre_alloc_group.pre[account]
                    self.pre_account_count += previous_pre_alloc_group.pre_account_count
                    self.test_count += previous_pre_alloc_group.test_count
                    self.test_ids.extend(previous_pre_alloc_group.test_ids)

            with open(file, "w") as f:
                f.write(self.model_dump_json(by_alias=True, exclude_none=True, indent=2))


class PreAllocGroups(EthereumTestRootModel):
    """Root model mapping pre-allocation group hashes to test groups."""

    root: Dict[str, PreAllocGroup]

    def __setitem__(self, key: str, value: Any):
        """Set item in root dict."""
        self.root[key] = value

    @classmethod
    def from_folder(cls, folder: Path) -> "PreAllocGroups":
        """Create PreAllocGroups from a folder of pre-allocation files."""
        data = {}
        for file in folder.glob("*.json"):
            with open(file) as f:
                data[file.stem] = PreAllocGroup.model_validate_json(f.read())
        return cls(root=data)

    def to_folder(self, folder: Path) -> None:
        """Save PreAllocGroups to a folder of pre-allocation files."""
        for key, value in self.root.items():
            value.to_file(folder / f"{key}.json")

    def __getitem__(self, item):
        """Get item from root dict."""
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

    def values(self):
        """Get values from root dict."""
        return self.root.values()

    def items(self):
        """Get items from root dict."""
        return self.root.items()
