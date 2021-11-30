"""
Sphinx extension to collect navigation metadata for hard forks.
"""

import os.path
from collections import defaultdict
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple

from sphinx.application import Sphinx
from sphinx.domains import Index, IndexEntry

import ethereum

from .forks import Hardfork


def _remove_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix) :]
    raise Exception(f"expected prefix {prefix}, but got {text}")


class _ForkEntry(NamedTuple):
    modules: List[IndexEntry]
    comparisons: List[IndexEntry]


class HardforkIndex(Index):
    """
    Collects metadata for hard forks.
    """

    name = "hardforks"
    localname = "Hard Fork Index"
    shortname = "Hard Fork"

    def generate(
        self, doc_names: Optional[Iterable[str]] = None
    ) -> Tuple[List[Tuple[str, List[IndexEntry]]], bool]:
        """
        Build an index.
        """
        forks = Hardfork.discover()

        content: Dict[Hardfork, _ForkEntry] = defaultdict(
            lambda: _ForkEntry(modules=[], comparisons=[])
        )

        comparisons = defaultdict(set)

        for name, _, kind, doc_name, _, _ in self.domain.get_objects():
            if kind != "module":
                continue

            fork = None

            for index, guess in enumerate(forks):
                if name.startswith(guess.name + "."):
                    fork = guess
                    break

            if fork is None:
                continue

            content[fork].modules.append(
                IndexEntry(
                    name,
                    2,
                    doc_name,
                    "",
                    "",
                    "",
                    "",
                )
            )

            base = "/".join(["autoapi", "ethereum", fork.short_name])
            rel_doc_name = os.path.relpath(doc_name, base)
            rel_name = _remove_prefix(name, fork.name)[1:]

            next_fork: Optional[Hardfork]

            try:
                next_fork = forks[index + 1]
            except IndexError:
                next_fork = None

            if next_fork:
                comparisons[(fork, next_fork)].add((rel_doc_name, rel_name))

            prev_fork = None
            if index > 0:
                prev_fork = forks[index - 1]

            if prev_fork:
                comparisons[(prev_fork, fork)].add((rel_doc_name, rel_name))

        for (prev_fork, fork), modules in comparisons.items():
            for (module, rel_name) in modules:
                doc_name = (
                    f"diffs/{prev_fork.short_name}_{fork.short_name}/{module}"
                )
                content[fork].comparisons.append(
                    IndexEntry(
                        rel_name,
                        2,
                        doc_name,
                        "",
                        "",
                        "",
                        "",
                    )
                )

        entries = sorted(content.items(), key=lambda i: i[0].block)

        result = []

        for fork, entry in entries:
            items: List[IndexEntry] = []
            result.append((fork.name, items))

            items.append(
                IndexEntry(
                    "Specification",
                    1,
                    "",
                    "",
                    "",
                    "",
                    "",
                )
            )
            items.extend(entry.modules)

            if not entry.comparisons:
                continue

            items.append(
                IndexEntry(
                    "Changes",
                    1,
                    "",
                    "",
                    "",
                    "",
                    "",
                )
            )
            items.extend(sorted(entry.comparisons, key=lambda i: i.name))

        return (result, True)


def setup(app: Sphinx) -> Dict[str, Any]:
    """
    Register the Sphinx plugin.
    """
    app.add_index_to_domain("py", HardforkIndex)

    return {
        "version": ethereum.__version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
