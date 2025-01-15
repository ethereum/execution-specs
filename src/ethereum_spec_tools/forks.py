"""
Ethereum Forks
^^^^^^^^^^^^^^

Detects Python packages that specify Ethereum hardforks.
"""

import importlib
import importlib.abc
import importlib.util
import pkgutil
from enum import Enum, auto
from pathlib import PurePath
from pkgutil import ModuleInfo
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
)

from ethereum_types.numeric import U256, Uint

if TYPE_CHECKING:
    from ethereum.fork_criteria import ForkCriteria


class ConsensusType(Enum):
    """
    How a fork chooses its canonical chain.
    """

    PROOF_OF_WORK = auto()
    PROOF_OF_STAKE = auto()

    def is_pow(self) -> bool:
        """
        Returns True if self == PROOF_OF_WORK.
        """
        return self == ConsensusType.PROOF_OF_WORK

    def is_pos(self) -> bool:
        """
        Returns True if self == PROOF_OF_STAKE.
        """
        return self == ConsensusType.PROOF_OF_STAKE


H = TypeVar("H", bound="Hardfork")


class Hardfork:
    """
    Metadata associated with an Ethereum hardfork.
    """

    mod: ModuleType

    @classmethod
    def discover(cls: Type[H], base: Optional[PurePath] = None) -> List[H]:
        """
        Find packages which contain Ethereum hardfork specifications.
        """
        if base is None:
            ethereum = importlib.import_module("ethereum")
        else:
            spec = importlib.util.spec_from_file_location(
                "ethereum", base / "__init__.py", submodule_search_locations=[]
            )
            if spec is None:
                raise ValueError("unable to find module from file")
            ethereum = importlib.util.module_from_spec(spec)
            if spec.loader and hasattr(spec.loader, "exec_module"):
                spec.loader.exec_module(ethereum)

        path = getattr(ethereum, "__path__", None)
        if path is None:
            raise ValueError("module `ethereum` has no path information")

        modules = pkgutil.iter_modules(path, ethereum.__name__ + ".")
        modules = (module for module in modules if module.ispkg)
        forks: List[H] = []

        for pkg in modules:
            # Use find_spec() to find the module specification.
            if isinstance(pkg.module_finder, importlib.abc.MetaPathFinder):
                found = pkg.module_finder.find_spec(pkg.name, None)
            elif isinstance(pkg.module_finder, importlib.abc.PathEntryFinder):
                found = pkg.module_finder.find_spec(pkg.name)
            else:
                raise Exception(
                    "unsupported module_finder "
                    f"`{type(pkg.module_finder).__name__}` while finding spec "
                    f"for `{pkg.name}`"
                )

            if not found:
                raise Exception(f"unable to find module spec for {pkg.name}")

            # Load the module from the spec.
            mod = importlib.util.module_from_spec(found)

            # Execute the module in its namespace.
            if found.loader:
                found.loader.exec_module(mod)
            else:
                raise Exception(f"No loader found for module {pkg.name}")

            if hasattr(mod, "FORK_CRITERIA"):
                forks.append(cls(mod))

        # Timestamps are bigger than block numbers, so this always works.
        forks.sort(key=lambda fork: fork.criteria)

        return forks

    @classmethod
    def load(cls: Type[H], config_dict: Dict["ForkCriteria", str]) -> List[H]:
        """
        Load the forks from a config dict specifying fork blocks and
        timestamps.
        """
        config = sorted(config_dict.items(), key=lambda x: x[0])

        forks = []

        for criteria, name in config:
            mod = importlib.import_module("ethereum." + name)
            mod.FORK_CRITERIA = criteria  # type: ignore
            forks.append(cls(mod))

        return forks

    @classmethod
    def load_from_json(cls: Type[H], json: Any) -> List[H]:
        """
        Load fork config from the json format used by Geth.

        Does not support some forks that only exist on Mainnet. Use
        `discover()` for Mainnet.
        """
        from ethereum.fork_criteria import ByBlockNumber, ByTimestamp

        c = json["config"]
        config = {
            ByBlockNumber(0): "frontier",
            ByBlockNumber(c["homesteadBlock"]): "homestead",
            ByBlockNumber(c["eip150Block"]): "tangerine_whistle",
            ByBlockNumber(c["eip155Block"]): "spurious_dragon",
            ByBlockNumber(c["byzantiumBlock"]): "byzantium",
            ByBlockNumber(c["constantinopleBlock"]): "constantinople",
            ByBlockNumber(c["istanbulBlock"]): "istanbul",
            ByBlockNumber(c["berlinBlock"]): "berlin",
            ByBlockNumber(c["londonBlock"]): "london",
            ByBlockNumber(c["mergeForkBlock"]): "paris",
            ByTimestamp(c["shanghaiTime"]): "shanghai",
        }

        if "daoForkBlock" in c:
            raise Exception(
                "Hardfork.load_from_json() does not support Mainnet"
            )

        return cls.load(config)

    def __init__(self, mod: ModuleType) -> None:
        self.mod = mod

    @property
    def consensus(self) -> ConsensusType:
        """
        How this fork chooses its canonical chain.
        """
        if hasattr(self.module("fork"), "validate_proof_of_work"):
            return ConsensusType.PROOF_OF_WORK
        else:
            return ConsensusType.PROOF_OF_STAKE

    @property
    def criteria(self) -> "ForkCriteria":
        """
        Criteria to trigger this hardfork.
        """
        from ethereum.fork_criteria import ForkCriteria

        criteria = self.mod.FORK_CRITERIA
        assert isinstance(criteria, ForkCriteria)
        return criteria

    @property
    def block(self) -> Uint:
        """
        Block number of the first block in this hard fork.
        """
        from ethereum.fork_criteria import ByBlockNumber

        if isinstance(self.criteria, ByBlockNumber):
            return self.criteria.block_number
        else:
            raise AttributeError

    @property
    def timestamp(self) -> U256:
        """
        Block number of the first block in this hard fork.
        """
        from ethereum.fork_criteria import ByTimestamp

        if isinstance(self.criteria, ByTimestamp):
            return self.criteria.timestamp
        else:
            raise AttributeError

    def has_activated(self, block_number: Uint, timestamp: U256) -> bool:
        """
        Check whether this fork has activated.
        """
        return self.criteria.check(block_number, timestamp)

    @property
    def path(self) -> Optional[str]:
        """
        Path to the module containing this hard fork.
        """
        got = getattr(self.mod, "__path__", None)
        if got is None or isinstance(got, str):
            return got

        try:
            assert isinstance(got[0], str)
            return got[0]
        except IndexError:
            return None

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
            + f"criteria={self.criteria}, "
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

        return pkgutil.walk_packages([self.path], self.name + ".")
