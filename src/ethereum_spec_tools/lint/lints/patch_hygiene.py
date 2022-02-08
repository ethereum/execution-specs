"""
Patch Hygiene Lint
^^^^^^^^^^^^^^^^^^

Ensures that the order of identifiers between each hardfork is consistent.
"""
import ast
from typing import List, Optional, OrderedDict, Sequence

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.lint import Diagnostic, Lint, walk_sources


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
        visitor = _Visitor()
        visitor.visit(parsed)
        return visitor.items


class _Visitor(ast.NodeVisitor):
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
