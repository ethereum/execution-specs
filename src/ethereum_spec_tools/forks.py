"""
Ethereum Forks
^^^^^^^^^^^^^^

Detects Python packages that specify Ethereum hardforks.
"""

import functools
import importlib
import pkgutil
from pkgutil import ModuleInfo
from types import ModuleType
from typing import Any, Dict, Iterator, List, Optional, Type, TypeVar

import ethereum

H = TypeVar("H", bound="Hardfork")


@functools.total_ordering
class ForkCriteria:
    """
    Type that represents the condition required for a fork to occur.
    """

    block_number: Optional[int]
    timestamp: Optional[int]

    def __init__(self) -> None:
        raise Exception("Can't be instantiated by __init__()")

    def __eq__(self, other: object) -> bool:
        """
        Equality for fork criteria.
        """
        if not isinstance(other, ForkCriteria):
            return NotImplemented
        return (
            self.block_number == other.block_number
            and self.timestamp == other.timestamp
        )

    def __lt__(self, other: object) -> bool:
        """
        Ordering for fork criteria. Block number forks are before timestamp
        forks and scheduled forks are before unscheduled forks.
        """
        if not isinstance(other, ForkCriteria):
            return NotImplemented
        if self.block_number is not None:
            if other.block_number is None:
                return True
            else:
                return self.block_number < other.block_number
        if self.timestamp is not None:
            if other.block_number is not None:
                return False
            elif other.timestamp is None:
                return True
            else:
                return self.timestamp < other.timestamp
        return False

    @classmethod
    def from_block_number(
        cls: Type["ForkCriteria"], block_number: int
    ) -> "ForkCriteria":
        """
        Criteria for a block number based fork.
        """
        self = ForkCriteria.__new__(cls)
        self.block_number = block_number
        self.timestamp = None
        return self

    @classmethod
    def from_timestamp(
        cls: Type["ForkCriteria"], timestamp: int
    ) -> "ForkCriteria":
        """
        Criteria for a timestamp based fork.
        """
        self = ForkCriteria.__new__(cls)
        self.block_number = None
        self.timestamp = timestamp
        return self

    @classmethod
    def never(cls: Type["ForkCriteria"]) -> "ForkCriteria":
        """
        Criteria for a fork that is not scheduled to happen.
        """
        self = ForkCriteria.__new__(cls)
        self.block_number = None
        self.timestamp = None
        return self

    def check(self, block_number: int, timestamp: int) -> bool:
        """
        Check whether fork criteria have been met.
        """
        if self.block_number is not None:
            return block_number >= self.block_number
        elif self.timestamp is not None:
            return timestamp >= self.timestamp
        else:
            return False


class Hardfork:
    """
    Metadata associated with an Ethereum hardfork.
    """

    mod: ModuleType
    criteria: ForkCriteria

    @classmethod
    def discover(cls: Type[H]) -> List[H]:
        """
        Find packages which contain Ethereum hardfork specifications.
        """
        path = getattr(ethereum, "__path__", None)
        if path is None:
            raise ValueError("module `ethereum` has no path information")

        modules = pkgutil.iter_modules(path, ethereum.__name__ + ".")
        modules = (module for module in modules if module.ispkg)
        forks: List[H] = []
        new_package = None

        for pkg in modules:
            mod = importlib.import_module(pkg.name)
            block = getattr(mod, "MAINNET_FORK_BLOCK", -1)
            timestamp = getattr(mod, "MAINNET_FORK_TIMESTAMP", -1)

            if block == -1 and timestamp == -1:
                continue

            # If the fork block is unknown, for example in a
            # new improvement proposal, it will be set as None.
            if block is None or timestamp is None:
                if new_package is not None:
                    raise ValueError(
                        "cannot have more than 1 new fork package."
                    )
                else:
                    new_package = cls(mod, ForkCriteria.never())
                continue

            if block is not None:
                forks.append(cls(mod, ForkCriteria.from_block_number(block)))
            else:
                forks.append(cls(mod, ForkCriteria.from_timestamp(timestamp)))

        # Timestamps are bigger than block numbers, so this always works.
        forks.sort(
            key=lambda fork: fork.block
            if hasattr(fork, "block")
            else fork.timestamp
        )
        if new_package is not None:
            forks.append(new_package)

        return forks

    @classmethod
    def load(cls: Type[H], config_dict: Dict[int, str]) -> List[H]:
        """
        Load the forks from a config dict specifying fork blocks and
        timestamps.
        """
        config = sorted(config_dict.items(), key=lambda x: x[0])

        forks = []

        for (block_or_time, name) in config:
            mod = importlib.import_module("ethereum." + name)

            if hasattr(mod, "MAINNET_FORK_BLOCK"):
                assert block_or_time < 1_000_000_000
                mod.MAINNET_FORK_BLOCK = block_or_time  # type: ignore
                criteria = ForkCriteria.from_block_number(block_or_time)
            else:
                assert block_or_time > 1_000_000_000
                mod.MAINNET_FORK_TIMESTAMP = block_or_time  # type: ignore
                criteria = ForkCriteria.from_timestamp(block_or_time)

            forks.append(cls(mod, criteria))

        return forks

    @classmethod
    def load_from_json(cls: Type[H], json: Any) -> List[H]:
        """
        Load fork config from the json format used by Geth.

        Does not support some forks that only exist on Mainnet. Use
        `discover()` for Mainnet.
        """
        c = json["config"]
        config = {
            0: "frontier",
            c["homesteadBlock"]: "homestead",
            c["eip150Block"]: "tangerine_whistle",
            c["eip155Block"]: "spurious_dragon",
            c["byzantiumBlock"]: "byzantium",
            c["constantinopleBlock"]: "constantinople",
            c["istanbulBlock"]: "istanbul",
            c["berlinBlock"]: "berlin",
            c["londonBlock"]: "london",
            c["mergeForkBlock"]: "paris",
            c["shanghaiTime"]: "shanghai",
        }

        if "daoForkBlock" in c:
            raise Exception(
                "Hardfork.load_from_json() does not support Mainnet"
            )

        return cls.load(config)

    def __init__(self, mod: ModuleType, criteria: ForkCriteria) -> None:
        self.mod = mod
        self.criteria = criteria

    @property
    def block(self) -> int:
        """
        Block number of the first block in this hard fork.
        """
        return getattr(self.mod, "MAINNET_FORK_BLOCK")  # noqa: B009

    @property
    def timestamp(self) -> int:
        """
        Block number of the first block in this hard fork.
        """
        return getattr(self.mod, "MAINNET_FORK_TIMESTAMP")  # noqa: B009

    def has_activated(self, block_number: int, timestamp: int) -> bool:
        """
        Check whether this fork has activated.
        """
        return self.criteria.check(block_number, timestamp)

    @property
    def path(self) -> Optional[str]:
        """
        Path to the module containing this hard fork.
        """
        return getattr(self.mod, "__path__", None)

    @property
    def short_name(self) -> str:
        """
        Short name (without the `ethereum.` prefix) of the hard fork.
        """
        return self.mod.__name__.split(".")[-1]

    @property
    def name(self) -> str:
        """
        Name of the hard fork.
        """
        return self.mod.__name__

    @property
    def title_case_name(self) -> str:
        """
        Name of the hard fork.
        """
        return self.short_name.replace("_", " ").title()

    def __repr__(self) -> str:
        """
        Return repr(self).
        """
        return (
            self.__class__.__name__
            + "("
            + f"name={self.name!r}, "
            + f"block={self.block}, "
            + "..."
            + ")"
        )

    def import_module(self) -> ModuleType:
        """
        Return the module containing this specification.
        """
        return self.mod

    def module(self, name: str) -> Any:
        """
        Import if necessary, and return the given module belonging to this hard
        fork.
        """
        return importlib.import_module(self.mod.__name__ + "." + name)

    def optimized_module(self, name: str) -> Any:
        """
        Import if necessary, and return the given module belonging to this hard
        fork's optimized implementation.
        """
        assert self.mod.__name__.startswith("ethereum.")
        module = "ethereum_optimized" + self.mod.__name__[8:] + "." + name
        return importlib.import_module(module)

    def iter_modules(self) -> Iterator[ModuleInfo]:
        """
        Iterate through the (sub-)modules describing this hardfork.
        """
        if self.path is None:
            raise ValueError(f"cannot walk {self.name}, path is None")

        return pkgutil.iter_modules(self.path, self.name + ".")

    def walk_packages(self) -> Iterator[ModuleInfo]:
        """
        Iterate recursively through the (sub-)modules describing this hardfork.
        """
        if self.path is None:
            raise ValueError(f"cannot walk {self.name}, path is None")

        return pkgutil.walk_packages(self.path, self.name + ".")
