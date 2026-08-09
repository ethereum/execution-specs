"""
Final Decorator Lint.

Ensures that leaf dataclasses are decorated with `@final`.
"""

import ast
import importlib
import inspect
import pkgutil
from typing import Generator, List, Optional, Sequence, Set, Tuple

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.lint import Diagnostic, Lint

DATACLASS_DECORATORS = {"dataclass", "slotted_freezable"}
FINAL_DECORATOR = "final"


def _spec_sources(
    forks: List[Hardfork],
) -> Generator[Tuple[str, str], None, None]:
    """
    Yield the name and source of every module in the specification.

    This spans each fork's modules as well as the shared, fork-independent
    modules such as `ethereum.state` and `ethereum.trace`. The fork packages
    are walked individually because `ethereum.forks` is a namespace package
    that `walk_packages` does not descend into from the `ethereum` root. The
    package roots are listed explicitly because `walk_packages` never yields
    the package it is walking, so their `__init__.py` files would otherwise
    be skipped.
    """
    names: List[str] = ["ethereum"]
    for fork in forks:
        names.append(fork.name)
        names += [mod_info.name for mod_info in fork.walk_packages()]

    root = importlib.import_module("ethereum")
    names += [
        mod_info.name
        for mod_info in pkgutil.walk_packages(root.__path__, "ethereum.")
    ]

    for name in names:
        mod = importlib.import_module(name)
        yield mod.__name__, inspect.getsource(mod)


class FinalDecoratorHygiene(Lint):
    """
    Ensure that every leaf dataclass is decorated with `@final`.

    A *leaf* class is one that is never used as a base class anywhere in the
    specification. Marking such classes `@final` lets `mypyc` bypass the
    vtable for method calls and property accessors. Classes that are
    subclassed are skipped (they are not leaves), as are non-dataclass types
    such as enums, protocols, exceptions, and constant namespaces.
    """

    def lint(
        self, forks: List[Hardfork], position: int
    ) -> Sequence[Diagnostic]:
        """
        Flag leaf dataclasses that are missing `@final`.

        The check spans every fork and the shared modules at once, so it only
        does work at the first position.
        """
        if position != 0:
            return []

        bases: Set[str] = set()
        candidates: List[Tuple[str, int, str]] = []
        for name, source in _spec_sources(forks):
            visitor = self._parse(source, _Visitor())
            bases |= visitor.bases
            for lineno, class_name in visitor.undecorated:
                candidates.append((name, lineno, class_name))

        diagnostics: List[Diagnostic] = []
        for name, lineno, class_name in candidates:
            if class_name in bases:
                # The class is subclassed somewhere, so it is not a leaf.
                continue
            diagnostics.append(
                Diagnostic(
                    message=(
                        f"`{class_name}` at line {lineno} in `{name}` is a "
                        "leaf dataclass and should be decorated with `@final`"
                    )
                )
            )

        return diagnostics


def _name_of(node: ast.expr) -> Optional[str]:
    """
    Return the bare name of a decorator or base class expression.

    Handles plain names (`final`), dotted names (`typing.final`), and calls
    (`dataclass(frozen=True)`). Returns `None` for anything else, such as a
    subscripted generic base.
    """
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


class _Visitor(ast.NodeVisitor):
    """
    Collect base class names and dataclasses that lack `@final`.
    """

    bases: Set[str]
    undecorated: List[Tuple[int, str]]

    def __init__(self) -> None:
        self.bases = set()
        self.undecorated = []

    def visit_ClassDef(self, klass: ast.ClassDef) -> None:
        """
        Visit a class definition.
        """
        for base in klass.bases:
            base_name = _name_of(base)
            if base_name is not None:
                self.bases.add(base_name)

        decorators: Set[str] = set()
        for decorator in klass.decorator_list:
            decorator_name = _name_of(decorator)
            if decorator_name is not None:
                decorators.add(decorator_name)

        if (
            decorators & DATACLASS_DECORATORS
            and FINAL_DECORATOR not in decorators
        ):
            self.undecorated.append((klass.lineno, klass.name))

        self.generic_visit(klass)
