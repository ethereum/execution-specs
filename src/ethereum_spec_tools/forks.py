"""
Ethereum Forks
^^^^^^^^^^^^^^

Detects Python packages that specify Ethereum hardforks.
"""

import importlib
import pkgutil
from pkgutil import ModuleInfo
from types import ModuleType
from typing import Iterator, List, Optional, Type, TypeVar

import ethereum

H = TypeVar("H", bound="Hardfork")


class Hardfork:
    """
    Metadata associated with an Ethereum hardfork.
    """

    mainnet_fork_block: int
    path: Optional[str]
    name: str

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
            path = getattr(mod, "__path__", None)

            if block is None:
                continue

            forks.append(cls(block, path, mod.__name__))

        forks.sort(key=lambda fork: fork.block)

        return forks

    def __init__(self, block: int, path: Optional[str], name: str) -> None:
        self.block = block
        self.path = path
        self.name = name

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
        Import and return the module containing this specification.
        """
        return importlib.import_module(self.name)

    def iter_modules(self) -> Iterator[ModuleInfo]:
        """
        Iterate through the (sub-)modules describing this hardfork.
        """
        if self.path is None:
            raise ValueError(f"cannot walk {self.name}, path is None")

        return pkgutil.iter_modules(self.path, self.name + ".")
