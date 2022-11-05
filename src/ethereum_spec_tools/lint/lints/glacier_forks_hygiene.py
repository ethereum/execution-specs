"""
Glacier Fork Hygiene Lint
^^^^^^^^^^^^^^^^^^^^^^^^^
Ensures that the glacier forks have changes only in BOMB_DELAY_BLOCKS.
"""
import ast
import sys
from typing import Dict, List, Sequence

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.lint import (
    Diagnostic,
    Lint,
    compare_ast,
    walk_sources,
)


class GlacierForksHygiene(Lint):
    """
    Ensures that the glacier forks have changes only in BOMB_DELAY_BLOCKS.
    """

    def __init__(self) -> None:
        self.delay_blocks = {
            "muir_glacier": 9000000,
            "arrow_glacier": 10700000,
            "gray_glacier": 11400000,
        }

    def lint(
        self, forks: List[Hardfork], position: int
    ) -> Sequence[Diagnostic]:
        """
        Walks the sources for each hardfork and emits Diagnostic messages.
        """
        fork_name = forks[position].short_name
        if not fork_name.endswith("_glacier"):
            # Nothing to compare against!
            return []

        diagnostics: List[Diagnostic] = []

        all_previous = dict(walk_sources(forks[position - 1]))
        all_current = dict(walk_sources(forks[position]))

        all_files = set(all_previous.keys()) | set(all_current.keys())
        for file in all_files:
            if file not in all_previous:
                self.add_diagnostic(
                    diagnostics,
                    (f"the file `{file}` is added to `{fork_name}`."),
                )
                continue

            if file not in all_current:
                self.add_diagnostic(
                    diagnostics,
                    (f"the file `{file}` is deleted from `{fork_name}`."),
                )
                continue

            current_node = self._parse(all_current[file], _Visitor(), "items")
            previous_node = self._parse(
                all_previous[file], _Visitor(), "items"
            )

            diagnostics += self.compare(
                fork_name, file, current_node, previous_node  # type: ignore
            )

        return diagnostics

    def compare(
        self, fork_name: str, name: str, current: Dict, previous: Dict
    ) -> List[Diagnostic]:
        """
        Compare nodes from two different modules for changes and
        emit diagnostics.
        """
        diagnostics: List[Diagnostic] = []

        all_items = set(previous.keys()) | set(current.keys())

        for item in all_items:
            try:
                previous_item = previous[item]
            except KeyError:
                self.add_diagnostic(
                    diagnostics, f"{item} in {name} has been added"
                )
                continue

            try:
                current_item = current[item]
            except KeyError:
                self.add_diagnostic(
                    diagnostics, f"{item} in {name} has been deleted"
                )
                continue

            if item == "BOMB_DELAY_BLOCKS":
                previous_item.value.value = self.delay_blocks[fork_name]

            if not compare_ast(previous_item, current_item):
                self.add_diagnostic(
                    diagnostics, f"the item `{item}` in `{name}` has changed"
                )

        return diagnostics


class _Visitor(ast.NodeVisitor):
    """
    Visits nodes in a syntax tree and collects functions, classes, and
    assignments.
    """

    path: List[str]
    _items: dict

    def __init__(self) -> None:
        self.path = []
        self._items = {}

    def generic_visit(self, node: ast.AST) -> None:
        """
        Called if no explicit visitor function exists for a node.
        Do not visit any child nodes.
        """
        sys.exit(f"No visit function defined for {node}")

    def _insert(self, name: str, node: ast.AST) -> None:
        item = ".".join(self.path + [name])
        if item in self._items:
            raise ValueError(f"duplicate path {item}")
        self._items[item] = node

    @property
    def items(self) -> Dict:
        """
        Sequence of all identifiers found while visiting the source.
        """
        return self._items

    def visit_Module(self, module: ast.Module) -> None:
        """
        Visit a python module.
        """
        for item in module.__dict__["body"]:
            if type(item) in (ast.Expr, ast.Import, ast.ImportFrom):
                continue
            self.visit(item)

    def visit_AsyncFunctionDef(self, function: ast.AsyncFunctionDef) -> None:
        """
        Visit an asynchronous function.
        """
        self._insert(function.name, function)

    def visit_FunctionDef(self, function: ast.FunctionDef) -> None:
        """
        Visit a function.
        """
        self._insert(function.name, function)

    def visit_ClassDef(self, klass: ast.ClassDef) -> None:
        """
        Visit a class.
        """
        self._insert(klass.name, klass)

    def visit_Assign(self, assign: ast.Assign) -> None:
        """
        Visit an assignment.
        """
        self._insert(assign.targets[0].id, assign)  # type: ignore

    def visit_AnnAssign(self, assign: ast.AnnAssign) -> None:
        """
        Visit an annotated assignment.
        """
        self._insert(assign.target.id, assign)  # type: ignore
