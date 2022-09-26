"""
Ethereum Forks
^^^^^^^^^^^^^^

Detects Python packages that specify Ethereum hardforks.
"""

import importlib
import pkgutil
from pkgutil import ModuleInfo
from types import ModuleType
from typing import Any, Dict, Iterator, List, Optional, Type, TypeVar

import ethereum

H = TypeVar("H", bound="Hardfork")


class Hardfork:
    """
    Metadata associated with an Ethereum hardfork.
    """

    mod: ModuleType

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

        for pkg in modules:
            mod = importlib.import_module(pkg.name)
            block = getattr(mod, "MAINNET_FORK_BLOCK", None)

            if block is None:
                continue

            forks.append(cls(mod, block))

        forks.sort(key=lambda fork: fork.block)

        return forks

    @classmethod
    def load(cls: Type[H], hardforks: Dict[int, ModuleType]) -> List[H]:
        """
        Find packages which contain Ethereum hardfork specifications.
        """
        forks: List[H] = []

        for (block, hardfork) in sorted(hardforks.items()):
            forks.append(cls(hardfork, block))

        return forks

    def __init__(self, mod: ModuleType, block: int) -> None:
        self.mod = mod
        self.block = block

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
