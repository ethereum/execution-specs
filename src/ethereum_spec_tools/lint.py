"""
Lints
^^^^^

Checks specific to the Ethereum specification source code.
"""

import ast
import importlib
import inspect
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Generator, List, Optional, Sequence, Tuple

from .forks import Hardfork
from .visitors import ImportHygieneVisitor, PatchHygieneVisitor


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


class PatchHygiene(Lint):
    """
    Ensures that the order of identifiers between each hardfork is consistent.
    """

    def lint(
        self, forks: List[Hardfork], position: int
    ) -> Sequence[Diagnostic]:
        """
        Walks the sources for each hardfork and emits Diagnostic messages.
        """
        if position == 0:
            # Nothing to compare against!
            return []

        all_previous = dict(walk_sources(forks[position - 1]))
        all_current = dict(walk_sources(forks[position]))

        items = (
            (k, v, all_previous.get(k, None)) for (k, v) in all_current.items()
        )

        diagnostics: List[Diagnostic] = []
        for (name, current, previous) in items:
            diagnostics += self.compare(name, current, previous)

        return diagnostics

    def compare(
        self, name: str, current_source: str, previous_source: Optional[str]
    ) -> List[Diagnostic]:
        """
        Compares two strings containing Python source and emits diagnostic
        messages if any identifiers have changed relative positions.
        """
        if previous_source is None:
            # Entire file is new, so nothing to compare!
            return []

        current_nodes = self.parse(current_source)
        previous_nodes = {
            item: idx for (idx, item) in enumerate(self.parse(previous_source))
        }

        diagnostics: List[Diagnostic] = []
        maximum = None

        for item in current_nodes:
            previous_position = previous_nodes.get(item)
            if previous_position is None:
                continue

            if maximum is None or previous_position > maximum:
                maximum = previous_position
            elif previous_position <= maximum:
                diagnostic = Diagnostic(
                    message=(
                        f"the item `{item}` in `{name}` has changed "
                        "relative positions"
                    )
                )
                diagnostics.append(diagnostic)

        return diagnostics

    def parse(self, source: str) -> Sequence[str]:
        """
        Walks the source string and extracts an ordered sequence of
        identifiers.
        """
        parsed = ast.parse(source)
        visitor = PatchHygieneVisitor()
        visitor.visit(parsed)
        return visitor.items


class ImportHygiene(Lint):
    """
    Ensures that the import statements follow the relevant rules.
    """

    def lint(
        self, forks: List[Hardfork], position: int
    ) -> Sequence[Diagnostic]:
        """
        Walks the sources for each hardfork and emits Diagnostic messages.
        """
        all_sources = dict(walk_sources(forks[position]))
        diagnostics: List[Diagnostic] = []
        for (name, source) in all_sources.items():
            diagnostics += self.check_import(forks, position, name, source)

        return diagnostics

    def check_import(
        self, forks: List[Hardfork], position: int, name: str, source: str
    ) -> List[Diagnostic]:
        """
        Checks a Python source and emits diagnostic
        messages if there are any invalid imports.
        """
        diagnostics: List[Diagnostic] = []

        active_fork = forks[position].name
        future_forks = tuple(fork.name for fork in forks[position + 1 :])
        ancient_forks = (
            tuple(fork.name for fork in forks[: position - 1])
            if position > 1
            else tuple()
        )

        current_imports = self.parse(source)

        for item in current_imports:
            if item is None:
                continue
            elif item.startswith(active_fork):
                diagnostic = Diagnostic(
                    message=(
                        f"The import `{item}` in `{name}` is "
                        "from the current fork. Please use a relative import."
                    )
                )
                diagnostics.append(diagnostic)

            elif item.startswith(future_forks):
                diagnostic = Diagnostic(
                    message=(
                        f"The import `{item}` in `{name}` "
                        "is from a future fork. This is not allowed."
                    )
                )
                diagnostics.append(diagnostic)
            elif item.startswith(ancient_forks):
                diagnostic = Diagnostic(
                    message=(
                        f"The import `{item}` in `{name}` is from an "
                        "older fork. Only imports from the previous "
                        "fork are allowed."
                    )
                )
                diagnostics.append(diagnostic)

        return diagnostics

    def parse(self, source: str) -> List[str]:
        """
        Walks the source string and extracts an ordered list of
        imports.
        """
        parsed = ast.parse(source)
        visitor = ImportHygieneVisitor()
        visitor.visit(parsed)
        return visitor.item_imports


class Linter:
    """
    Checks the specification for style guideline violations.
    """

    ALL_LINTS: List[Lint] = [PatchHygiene(), ImportHygiene()]

    lints: Sequence[Lint]

    def __init__(self, lints: Sequence[Lint] = ALL_LINTS) -> None:
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


if __name__ == "__main__":
    import sys

    sys.exit(main())
