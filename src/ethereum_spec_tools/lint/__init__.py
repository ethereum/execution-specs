"""
Lints
^^^^^

Checks specific to the Ethereum specification source code.
"""

import importlib
import inspect
import pkgutil
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Generator, List, Optional, Sequence, Tuple

from ..forks import Hardfork


def walk_sources(fork: Hardfork) -> Generator[Tuple[str, str], None, None]:
    """
    Import the modules specifying a hardfork, and retrieve their source code.
    """
    for mod_info in fork.walk_packages():
        mod = importlib.import_module(mod_info.name)
        source = inspect.getsource(mod)
        name = mod.__name__
        if name.startswith(fork.name):
            name = name[len(fork.name) :]
        yield (name, source)


@dataclass
class Diagnostic:
    """
    A diagnostic message generated while checking the specifications.
    """

    message: str


class Lint(metaclass=ABCMeta):
    """
    A single check which may be performed against the specifications.
    """

    @abstractmethod
    def lint(
        self, forks: List[Hardfork], position: int
    ) -> Sequence[Diagnostic]:
        """
        Runs the check against the given forks, at the given position.

        Parameters
        ----------
        forks :
            All known hardforks.
        position :
            The particular hardfork to lint.
        """


class Linter:
    """
    Checks the specification for style guideline violations.
    """

    lints: Sequence[Lint]

    @staticmethod
    def discover_lints() -> Sequence[Lint]:
        """
        Discover subclasses of Lint.
        """
        from . import lints

        path = getattr(lints, "__path__", None)

        if path is None:
            return []

        modules = pkgutil.iter_modules(path, lints.__name__ + ".")
        for finder, name, ispkg in modules:
            try:
                importlib.import_module(name)
            except Exception:
                continue

        found = set()
        for subclass in Lint.__subclasses__():
            if inspect.isabstract(subclass):
                continue

            try:
                found.add(subclass())  # type: ignore[abstract]
            except Exception:
                pass

        return list(found)

    def __init__(self, lints: Optional[Sequence[Lint]] = None) -> None:
        if lints is None:
            lints = Linter.discover_lints()

        if not lints:
            raise Exception("no lints specified")

        self.lints = lints

    def run(self) -> int:
        """
        Runs all enabled lints.
        """
        count = 0
        hardforks = Hardfork.discover()

        for lint in self.lints:
            diagnostics: List[Diagnostic] = []
            for hardfork in range(0, len(hardforks)):
                diagnostics += lint.lint(hardforks, hardfork)

                if diagnostics:
                    count += len(diagnostics)
                    print(
                        f"{hardforks[hardfork].name} - "
                        f"{lint.__class__.__name__}:"
                    )
                    for diagnostic in diagnostics:
                        print("\t", diagnostic.message)

                    diagnostics = []

        if count > 0:
            print("Total diagnostics:", count)

        return 1 if count > 0 else 0


def main() -> int:
    """
    `ethereum-spec-lint` checks for style and formatting issues specific to the
    Ethereum specification.
    """
    linter = Linter()
    return linter.run()
