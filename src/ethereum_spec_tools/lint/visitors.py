"""
Visitors
^^^^^

Defines node visitors for the various Lint subclasses.
"""
import ast
from collections import OrderedDict
from typing import List, Sequence


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


class ImportHygieneVisitor(ast.NodeVisitor):
    """
    Visits nodes in a syntax tree and collects functions, classes, and
    assignments.
    """

    item_imports: List[str]

    def __init__(self) -> None:
        self.item_imports = []

    def visit_Import(self, mod: ast.Import) -> None:
        """
        Visit an Import.
        """
        self.item_imports.append(mod.names[0].name)

    def visit_ImportFrom(self, mod: ast.ImportFrom) -> None:
        """
        Visit an ImportFrom.
        """
        self.item_imports.append(str(mod.module))
