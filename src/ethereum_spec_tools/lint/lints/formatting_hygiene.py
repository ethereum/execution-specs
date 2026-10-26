"""
Formatting Hygiene Lint.

Ensures that consecutive hardforks don't differ only in formatting.
"""

import difflib
import io
import re
import tokenize
from typing import Dict, List, Optional, Sequence

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.lint import Diagnostic, Lint, walk_sources

# Spacing around these characters doesn't change the meaning of the code.
_PUNCTUATION = re.compile(r" ?([()\[\]{},:]) ?")
_TRAILING_COMMA = re.compile(r",([)\]}])")


def statement_indents(source: str) -> Dict[int, int]:
    """
    Map the index of each line that starts a statement to its indentation.

    Indentation is meaningful there, unlike on continuation lines inside
    brackets or inside multi-line strings.
    """
    indents: Dict[int, int] = {}
    at_start = True
    readline = io.StringIO(source).readline
    for token in tokenize.generate_tokens(readline):
        if token.type in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
            at_start = True
        elif token.type not in (tokenize.NL, tokenize.COMMENT):
            if at_start:
                indents[token.start[0] - 1] = token.start[1]
            at_start = False
    return indents


def squash_formatting(
    lines: Sequence[str], indents: Sequence[Optional[int]]
) -> str:
    """
    Reduce `lines` to a form that ignores layout.

    Whitespace and line breaks collapse to single spaces, and spaces next
    to brackets, commas and colons are dropped, as are trailing commas.
    The indentation of a line that starts a statement, given in `indents`
    (`None` for other lines), is kept because it decides which block the
    statement belongs to. Two pieces of code that squash to the same
    string differ only in formatting.
    """
    marked = [
        line if indent is None else f"<{indent}>{line}"
        for line, indent in zip(lines, indents, strict=True)
    ]
    text = re.sub(r"\s+", " ", "\n".join(marked)).strip()
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

        previous = forks[position - 1].short_name
        all_previous = dict(walk_sources(forks[position - 1]))

        diagnostics: List[Diagnostic] = []
        for name, source in walk_sources(forks[position]):
            diagnostics += self.compare(
                name, source, all_previous.get(name), previous
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

        # Split on newlines only, so that line numbers match `tokenize`.
        previous_lines = previous_source.split("\n")
        current_lines = current_source.split("\n")
        previous_indents = statement_indents(previous_source)
        current_indents = statement_indents(current_source)
        matcher = difflib.SequenceMatcher(
            a=previous_lines, b=current_lines, autojunk=False
        )

        diagnostics: List[Diagnostic] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            previous_squashed = squash_formatting(
                previous_lines[i1:i2],
                [previous_indents.get(i) for i in range(i1, i2)],
            )
            current_squashed = squash_formatting(
                current_lines[j1:j2],
                [current_indents.get(j) for j in range(j1, j2)],
            )
            if previous_squashed != current_squashed:
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
