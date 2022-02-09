"""
Import Hygiene Lint
^^^^^^^^^^^^^^^^^^^

Ensures that the import statements follow the relevant rules.
"""
import ast
from typing import List, Sequence

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.lint import Diagnostic, Lint, walk_sources


class ImportHygiene(Lint):
    """
    Ensures that the import statements follow the relevant rules.

    The rules when inside a hard fork file:

     - Deny absolute imports from within the active fork.
     - Deny absolute imports from future forks.
     - Deny absolute imports from active-minus-two and earlier hard forks.
     - Allow relative imports from the active hard fork.
     - Allow absolute imports from the active-minus-one hard fork.
     - Allow absolute imports of non-fork specific things.
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

        current_imports = self._parse(source, _Visitor(), "item_imports")

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


class _Visitor(ast.NodeVisitor):
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
