"""
Ethereum Forks.

Detects Python packages that specify Ethereum hardforks.
"""

import importlib
import importlib.abc
import importlib.util
import pkgutil
import random
import sys
from contextlib import AbstractContextManager
from enum import Enum, auto
from importlib.machinery import ModuleSpec, PathFinder
from pathlib import Path
from pkgutil import ModuleInfo
from tempfile import TemporaryDirectory
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
    Union,
    cast,
)

from ethereum_types.numeric import U64, U256, Uint
from typing_extensions import override

if TYPE_CHECKING:
    from ethereum.fork_criteria import (
        ByBlockNumber,
        ByTimestamp,
        ForkCriteria,
        Unscheduled,
    )


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
    def discover(
        cls: Type[H], submodule_search_locations: None | list[str] = None
    ) -> List[H]:
        """
        Find packages which contain Ethereum hardfork specifications.
        """
        if submodule_search_locations is None:
            ethereum_forks = importlib.import_module("ethereum.forks")
        else:
            spec = ModuleSpec("ethereum.forks", loader=None, is_package=True)
            spec.submodule_search_locations = submodule_search_locations

            ethereum_forks = importlib.util.module_from_spec(spec)
            if spec.loader and hasattr(spec.loader, "exec_module"):
                spec.loader.exec_module(ethereum_forks)

        path = getattr(ethereum_forks, "__path__", None)
        if path is None:
            raise ValueError("module `ethereum` has no path information")

        modules = pkgutil.iter_modules(path, ethereum_forks.__name__ + ".")
        modules = (module for module in modules if module.ispkg)
        forks: List[H] = []

        for pkg in modules:
            try:
                mod = sys.modules[pkg.name]
                if hasattr(mod, "FORK_CRITERIA"):
                    forks.append(cls(mod))
                continue
            except KeyError:
                pass

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

            sys.modules[pkg.name] = mod

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

    @staticmethod
    def clone(
        template: H | str,
        fork_criteria: Union[
            "ByBlockNumber", "ByTimestamp", "Unscheduled", None
        ] = None,
        target_blob_gas_per_block: U64 | None = None,
        gas_per_blob: U64 | None = None,
        min_blob_gasprice: Uint | None = None,
        blob_base_fee_update_fraction: Uint | None = None,
        max_blob_gas_per_block: U64 | None = None,
        blob_schedule_target: U64 | None = None,
        blob_schedule_max: U64 | None = None,
    ) -> "TemporaryHardfork":
        """
        Create a temporary clone of an existing fork, optionally tweaking its
        parameters.
        """
        from .new_fork.builder import ForkBuilder

        maybe_directory: TemporaryDirectory | None = TemporaryDirectory()

        try:
            assert maybe_directory is not None
            directory: TemporaryDirectory = maybe_directory

            if isinstance(template, str):
                template_name = template
            else:
                template_name = template.short_name

            clone_name = (
                f"{template_name}_clone{random.randrange(1_000_000_000)}"
            )

            builder = ForkBuilder(template_name, clone_name)

            builder.output = Path(directory.name)

            if fork_criteria is not None:
                builder.fork_criteria = fork_criteria

            if target_blob_gas_per_block is not None:
                builder.modify_target_blob_gas_per_block(
                    target_blob_gas_per_block
                )

            if gas_per_blob is not None:
                builder.modify_gas_per_blob(gas_per_blob)

            if min_blob_gasprice is not None:
                builder.modify_min_blob_gasprice(min_blob_gasprice)

            if blob_base_fee_update_fraction is not None:
                builder.modify_blob_base_fee_update_fraction(
                    blob_base_fee_update_fraction
                )

            if max_blob_gas_per_block is not None:
                builder.modify_max_blob_gas_per_block(max_blob_gas_per_block)

            if blob_schedule_target is not None:
                builder.modify_blob_schedule_target(blob_schedule_target)

            if blob_schedule_max is not None:
                builder.modify_blob_schedule_max(blob_schedule_max)

            builder.build()

            clone_forks = Hardfork.discover([directory.name])
            if len(clone_forks) != 1:
                raise Exception("len(clone_forks) != 1")
            if clone_forks[0].short_name != clone_name:
                raise Exception("found incorrect fork")

            value = TemporaryHardfork(clone_forks[0].mod, directory)
            maybe_directory = None
            return value
        finally:
            if maybe_directory is not None:
                maybe_directory.cleanup()

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
        Timestamp of the first block in this hard fork.
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
        if self.short_name.startswith("bpo"):
            return "BPO" + self.short_name[3:].replace("_", " ")

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
        # Handle the "already imported" case early.
        full_name = self.mod.__name__ + "." + name
        try:
            return sys.modules[full_name]
        except KeyError:
            pass

        # Import each package (including parents), returning the last one.
        fragments = name.split(".")
        mod = self.mod

        for fragment in fragments:
            name = mod.__name__ + "." + fragment
            try:
                mod = sys.modules[name]
                continue
            except KeyError:
                pass

            if mod.__spec__ is None:
                raise ImportError(f"{mod.__name__} is not a package")
            if mod.__spec__.submodule_search_locations is None:
                raise ImportError(f"{mod.__name__} is not a package")

            spec = PathFinder.find_spec(
                name,
                path=mod.__spec__.submodule_search_locations,
                target=mod,
            )
            if spec is None or spec.loader is None:
                raise ModuleNotFoundError(name)

            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            if spec.loader and hasattr(spec.loader, "exec_module"):
                spec.loader.exec_module(mod)

        assert mod.__name__ == full_name
        return mod

    def iter_modules(self) -> Iterator[ModuleInfo]:
        """
        Iterate through the (sub-)modules describing this hardfork.
        """
        if self.mod.__path__ is None:
            raise ValueError(f"cannot walk {self.name}, path is None")

        return pkgutil.iter_modules(self.mod.__path__, self.name + ".")

    def walk_packages(self) -> Iterator[ModuleInfo]:
        """
        Iterate recursively through the (sub-)modules describing this hardfork.
        """
        if self.mod.__path__ is None:
            raise ValueError(f"cannot walk {self.name}, path is None")

        return pkgutil.walk_packages(self.mod.__path__, self.name + ".")


class TemporaryHardfork(Hardfork, AbstractContextManager):
    """
    Short-lived `Hardfork` located in a temporary directory.
    """

    directory: TemporaryDirectory | None

    def __init__(self, mod: ModuleType, directory: TemporaryDirectory) -> None:
        super().__init__(mod)
        self.directory = directory

    @override
    def __exit__(self, *args: object, **kwargs: object) -> None:
        del args
        del kwargs

        assert self.directory is not None
        self.directory.cleanup()
        self.directory = None

        # Intentionally break ourselves. Once the directory is gone, imports
        # won't work.
        self.mod = cast(ModuleType, None)
