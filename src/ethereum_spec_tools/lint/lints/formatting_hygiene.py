"""
Formatting Hygiene Lint.

Ensures that consecutive hardforks don't differ only in formatting.
"""

import difflib
import re
from typing import List, Optional, Sequence, Set, Tuple

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.lint import Diagnostic, Lint, walk_sources

# Modules allowed to differ only in formatting from the same module in the
# previous hardfork, as `(fork, module)` pairs. Each entry should be removed
# once the difference is fixed; the lint reports entries that are no longer
# needed.
EXCEPTIONS: Set[Tuple[str, str]] = {
    # Call layout in `system.py` (#2681).
    ("arrow_glacier", ".vm.instructions.system"),
    ("gray_glacier", ".vm.instructions.system"),
    ("shanghai", ".vm.instructions.system"),
    ("osaka", ".vm.instructions.system"),
    ("bpo1", ".vm.instructions.system"),
    ("bpo2", ".vm.instructions.system"),
    ("bpo4", ".vm.instructions.system"),
    # Wrapping of the `check_gas_limit` docstring (#2681).
    ("homestead", ".fork"),
    ("istanbul", ".fork"),
    ("london", ".fork"),
    ("prague", ".fork"),  # Also a blank line.
    # Blank lines.
    ("istanbul", ".utils.address"),
    ("london", ".vm.interpreter"),
    ("arrow_glacier", ".vm.interpreter"),
    ("shanghai", ".transactions"),
    ("osaka", ".vm.eoa_delegation"),
    ("bpo1", ".vm.eoa_delegation"),
    ("amsterdam", ".vm.eoa_delegation"),
    ("amsterdam", ".vm.instructions.system"),
}

# Spacing around these characters doesn't change the meaning of the code.
_PUNCTUATION = re.compile(r" ?([()\[\]{},:]) ?")
_TRAILING_COMMA = re.compile(r",([)\]}])")


def squash_formatting(lines: Sequence[str]) -> str:
    """
    Reduce `lines` to a form that ignores layout.

    Whitespace and line breaks collapse to single spaces, and spaces next
    to brackets, commas and colons are dropped, as are trailing commas.
    Two pieces of code that squash to the same string differ only in
    formatting.
    """
    text = re.sub(r"\s+", " ", "\n".join(lines)).strip()
    text = _PUNCTUATION.sub(r"\1", text)
    text = _TRAILING_COMMA.sub(r"\1", text)
    return text.rstrip(",")


class FormattingHygiene(Lint):
    """
    Ensures that consecutive hardforks don't differ only in formatting.

    A change that only reformats code (line breaks, trailing commas, blank
    lines or re-wrapped docstrings) belongs in every hardfork or in none,
    so that the diff between two hardforks shows only what changed.
    """

    def lint(
        self, forks: List[Hardfork], position: int
    ) -> Sequence[Diagnostic]:
        """
        Compare each module of a hardfork with its previous hardfork.
        """
        if position == 0:
            # Nothing to compare against!
            return []

        fork = forks[position].short_name
        previous = forks[position - 1].short_name
        all_previous = dict(walk_sources(forks[position - 1]))

        diagnostics: List[Diagnostic] = []
        for name, source in walk_sources(forks[position]):
            found = self.compare(
                name, source, all_previous.get(name), previous
            )

            if (fork, name) not in EXCEPTIONS:
                diagnostics += found
            elif not found:
                diagnostics.append(
                    Diagnostic(
                        message=(
                            f"`{name}` no longer differs from `{previous}` "
                            "only in formatting; remove it from `EXCEPTIONS`"
                        )
                    )
                )

        return diagnostics

    def compare(
        self,
        name: str,
        current_source: str,
        previous_source: Optional[str],
        previous_fork: str,
    ) -> List[Diagnostic]:
        """
        Report each part of `current_source` that differs from
        `previous_source` only in formatting.
        """
        if previous_source is None:
            # Entire file is new, so nothing to compare!
            return []

        previous_lines = previous_source.splitlines()
        current_lines = current_source.splitlines()
        matcher = difflib.SequenceMatcher(
            a=previous_lines, b=current_lines, autojunk=False
        )

        diagnostics: List[Diagnostic] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            if squash_formatting(previous_lines[i1:i2]) != squash_formatting(
                current_lines[j1:j2]
            ):
                continue
            diagnostics.append(
                Diagnostic(
                    message=(
                        f"`{name}` line {j1 + 1} differs from "
                        f"`{previous_fork}` only in formatting"
                    )
                )
            )

        return diagnostics
