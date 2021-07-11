"""
Lints
^^^^^

Checks specific to the Ethereum specification source code.
"""

import ast
import importlib
import inspect
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from typing import Generator, List, Optional, Sequence, Tuple

from .forks import Hardfork


def walk_sources(fork: Hardfork) -> Generator[Tuple[str, str], None, None]:
    """
    Import the modules specifying a hardfork, and retrieve their source code.
    """
    for mod_info in fork.iter_modules():
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


class PatchHygieneVisitor(ast.NodeVisitor):
    """
    Visits nodes in a syntax tree and collects functions, classes, and
    assignments.
    """

    path: List[str]
    _items: "OrderedDict[str, None]"
    in_assign: int

    def __init__(self) -> None:
        self.path = []
        self._items = OrderedDict()
        self.in_assign = 0

    def _insert(self, item: str) -> None:
        item = ".".join(self.path + [item])
        if item in self._items:
            raise ValueError(f"duplicate path {item}")
        self._items[item] = None

    @property
    def items(self) -> Sequence[str]:
        """
        Sequence of all identifiers found while visiting the source.
        """
        return list(self._items.keys())

    def visit_AsyncFunctionDef(self, function: ast.AsyncFunctionDef) -> None:
        """
        Visit an asynchronous function.
        """
        self._insert(function.name)
        # Explicitly don't visit the children of functions.

    def visit_FunctionDef(self, function: ast.FunctionDef) -> None:
        """
        Visit a function.
        """
        self._insert(function.name)
        # Explicitly don't visit the children of functions.

    def visit_ClassDef(self, klass: ast.ClassDef) -> None:
        """
        Visit a class.
        """
        self._insert(klass.name)
        self.path.append(klass.name)
        self.generic_visit(klass)
        got = self.path.pop()
        assert klass.name == got

    def visit_Assign(self, assign: ast.Assign) -> None:
        """
        Visit an assignment.
        """
        self.in_assign += 1
        for target in assign.targets:
            self.visit(target)
        self.in_assign -= 1
        self.visit(assign.value)

    def visit_AnnAssign(self, assign: ast.AnnAssign) -> None:
        """
        Visit an annotated assignment.
        """
        self.in_assign += 1
        self.visit(assign.target)
        self.in_assign -= 1
        self.visit(assign.annotation)
        if assign.value is not None:
            self.visit(assign.value)

    def visit_Name(self, identifier: ast.Name) -> None:
        """
        Visit an identifier.
        """
        if self.in_assign > 0:
            self._insert(identifier.id)


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


class Linter:
    """
    Checks the specification for style guideline violations.
    """

    ALL_LINTS: List[Lint] = [
        PatchHygiene(),
    ]

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
                    f"{hardforks[hardfork].name} - {lint.__class__.__name__}:"
                )
                for diagnostic in diagnostics:
                    print("\t", diagnostic.message)

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
