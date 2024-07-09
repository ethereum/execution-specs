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

EXCEPTIONAL_FILES = [
    ("dao_fork", ".dao"),
]

EXCEPTIONAL_DIFFS = [
    # The DAO Fork has an irregular state transition and minor changes to the
    # graffiti near the fork block.
    ("dao_fork", ".fork", "apply_fork"),
    ("dao_fork", ".fork", "validate_header"),
    # There are some differences between london and arrow_glacier
    # in terms of how the fork block is handled.
    ("arrow_glacier", ".fork", "calculate_base_fee_per_gas"),
    ("arrow_glacier", ".fork", "validate_header"),
    ("arrow_glacier", ".fork", "INITIAL_BASE_FEE"),
]


def add_diagnostic(diagnostics: List[Diagnostic], message: str) -> None:
    """
    Adds a new diagnostic message.
    """
    diagnostic = Diagnostic(message=message)
    diagnostics.append(diagnostic)


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
        if position == 0:
            # Nothing to compare against!
            return []

        if fork_name != "dao_fork" and not fork_name.endswith("_glacier"):
            # Nothing to compare against or non-glacier fork!
            return []

        diagnostics: List[Diagnostic] = []

        all_previous = dict(walk_sources(forks[position - 1]))
        all_current = dict(walk_sources(forks[position]))

        all_files = set(all_previous.keys()) | set(all_current.keys())
        for file in all_files:
            if (fork_name, file) in EXCEPTIONAL_FILES:
                continue

            if file not in all_previous:
                add_diagnostic(
                    diagnostics,
                    f"the file `{file}` is added to `{fork_name}`. "
                    "Glacier forks may only differ in difficulty block.",
                )
                continue

            if file not in all_current:
                add_diagnostic(
                    diagnostics,
                    f"the file `{file}` is deleted from `{fork_name}`. "
                    "Glacier forks may only differ in difficulty block.",
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
            if (fork_name, name, item) in EXCEPTIONAL_DIFFS:
                continue
            try:
                previous_item = previous[item]
            except KeyError:
                add_diagnostic(
                    diagnostics,
                    f"{item} in {name} has been added. "
                    "Glacier forks may only differ in difficulty block.",
                )
                continue

            try:
                current_item = current[item]
            except KeyError:
                add_diagnostic(
                    diagnostics,
                    f"{item} in {name} has been deleted. "
                    "Glacier forks may only differ in difficulty block.",
                )
                continue

            if item == "BOMB_DELAY_BLOCKS":
                previous_item.value.value = self.delay_blocks[fork_name]

            if not compare_ast(previous_item, current_item):
                add_diagnostic(
                    diagnostics,
                    f"`{item}` in `{name}` has changed. "
                    "Glacier forks may only differ in difficulty block.",
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
        sys.exit(
            f"No visit function defined for {node}. Please implement one."
        )

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
            self.visit(item)

    def visit_Import(self, import_: ast.Import) -> None:
        """
        Visit an Import
        """
        pass

    def visit_ImportFrom(self, import_from: ast.ImportFrom) -> None:
        """
        Visit an Import From
        """
        pass

    def visit_Expr(self, expr: ast.Expr) -> None:
        """
        Visit an Expression
        """
        # This is a way to identify comments in the current specs code
        # ignore comments
        if isinstance(expr.value, ast.Constant) and isinstance(
            expr.value.value, str
        ):
            return

        print(f"The expression {type(expr)} has been ignored.")

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
        if isinstance(assign.targets[0], ast.Name):
            self._insert(assign.targets[0].id, assign)
        else:
            print(
                "Assign node with target of type "
                f"{type(assign.targets[0])} has been ignored."
            )

    def visit_AnnAssign(self, assign: ast.AnnAssign) -> None:
        """
        Visit an annotated assignment.
        """
        if isinstance(assign.target, ast.Name):
            self._insert(assign.target.id, assign)
        else:
            print(
                f"AnnAssign node with target of type {type(assign.target)}"
                " has been ignored."
            )

    def visit_If(self, node: ast.If) -> None:
        """
        Visit an if statement.
        """
        for child in node.body:
            self.visit(child)
        for child in node.orelse:
            self.visit(child)
