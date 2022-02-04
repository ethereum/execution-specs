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


class PatchHygieneVisitor(ast.NodeVisitor):
    """
    Visits nodes in a syntax tree and collects functions, classes, and
    assignments.
    """

    path: List[str]
    _items: "OrderedDict[str, None]"
    in_assign: int
    item_imports: List[str]

    def __init__(self) -> None:
        self.path = []
        self._items = OrderedDict()
        self.in_assign = 0
        self.item_imports = []

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

        # Detect imports inside function body
        for node in function.body:
            if isinstance(node, ast.ImportFrom):
                self.item_imports.append(node.module)
            if isinstance(node, ast.Import):
                self.item_imports.append(node.names[0].name)

    def visit_FunctionDef(self, function: ast.FunctionDef) -> None:
        """
        Visit a function.
        """
        self._insert(function.name)

        # Detect imports inside function body
        for node in function.body:
            if isinstance(node, ast.ImportFrom):
                self.item_imports.append(node.module)
            if isinstance(node, ast.Import):
                self.item_imports.append(node.names[0].name)

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

    def visit_Import(self, mod: ast.Import) -> None:
        """
        Visit an Import.
        """
        self.item_imports.append(mod.names[0].name)

    def visit_ImportFrom(self, mod: ast.ImportFrom) -> None:
        """
        Visit an ImportFrom.
        """
        self.item_imports.append(mod.module)


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

        all_current = dict(walk_sources(forks[position]))
        diagnostics: List[Diagnostic] = []
        if position == 0:
            for (name, source) in all_current.items():
                # No need to run compare since this is the first fork
                diagnostics += self.check_import(forks, position, name, source)
        else:
            all_previous = dict(walk_sources(forks[position - 1]))

            items = (
                (k, v, all_previous.get(k, None))
                for (k, v) in all_current.items()
            )

            for (name, current, previous) in items:
                diagnostics += self.compare(name, current, previous)
                diagnostics += self.check_import(
                    forks, position, name, current
                )

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

        current_nodes = self.parse(current_source).items
        previous_nodes = {
            item: idx
            for (idx, item) in enumerate(self.parse(previous_source).items)
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

    def check_import(
        self, forks: List[Hardfork], position: int, name: str, source: str
    ) -> List[Diagnostic]:
        """
        Checks a Python source and emits diagnostic
        messages if there are any invalid imports.
        """

        diagnostics: List[Diagnostic] = []

        invalid_imports = {
            "active_fork": forks[position].name,
            "future_fork": tuple(fork.name for fork in forks[position + 1 :]),
            "minus2_fork": tuple(fork.name for fork in forks[: position - 1])
            if position > 1
            else tuple(),
        }

        current_imports = self.parse(source).item_imports

        for item in current_imports:
            if item is None:
                continue
            elif item.startswith(invalid_imports["active_fork"]):
                diagnostic = Diagnostic(
                    message=(
                        f"The import `{item}` in `{name}` is "
                        "from the current fork. Please use a relative import."
                    )
                )
                diagnostics.append(diagnostic)

            elif item.startswith(invalid_imports["future_fork"]):
                diagnostic = Diagnostic(
                    message=(
                        f"The import `{item}` in `{name}` "
                        "is from a future fork. This is not allowed."
                    )
                )
                diagnostics.append(diagnostic)
            elif item.startswith(invalid_imports["minus2_fork"]):
                diagnostic = Diagnostic(
                    message=(
                        f"The import `{item}` in `{name}` is from an older fork."
                        " Only imports from the previous fork are allowed."
                    )
                )
                diagnostics.append(diagnostic)

        return diagnostics

    def parse(self, source: str) -> PatchHygieneVisitor:
        """
        Walks the source string and extracts an ordered sequence of
        identifiers as well as the relevant imports within a PatchHygieneVisitor.
        """
        parsed = ast.parse(source)
        visitor = PatchHygieneVisitor()
        visitor.visit(parsed)
        return visitor


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
