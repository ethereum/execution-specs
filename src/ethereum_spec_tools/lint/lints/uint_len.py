"""
Uint(len(...)) Lint.

Ensures that `Uint(len(...))` is replaced with `ulen(...)`.
"""

import ast
from typing import List, Sequence

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.lint import Diagnostic, Lint, walk_sources


class UintLenHygiene(Lint):
    """
    Ensure `ulen(...)` is used instead of `Uint(len(...))`.
    """

    def lint(
        self, forks: List[Hardfork], position: int
    ) -> Sequence[Diagnostic]:
        """
        Walk the sources for each hardfork and emit Diagnostic messages.
        """
        fork = forks[position]
        diagnostics: List[Diagnostic] = []

        for name, source in walk_sources(fork):
            visitor = self._parse(source, _Visitor())
            for lineno in visitor.violations:
                diagnostics.append(
                    Diagnostic(
                        message=(
                            f"`Uint(len(...))` at line {lineno} in"
                            f" `{name}` should be `ulen(...)`"
                        )
                    )
                )

        return diagnostics


class _Visitor(ast.NodeVisitor):
    """
    Visit call nodes and detect `Uint(len(...))` patterns.
    """

    violations: List[int]

    def __init__(self) -> None:
        self.violations = []

    def visit_Call(self, node: ast.Call) -> None:
        """
        Visit a Call node.
        """
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "Uint"
            and len(node.args) == 1
            and not node.keywords
            and isinstance(node.args[0], ast.Call)
            and isinstance(node.args[0].func, ast.Name)
            and node.args[0].func.id == "len"
        ):
            self.violations.append(node.lineno)

        self.generic_visit(node)
