"""
Tests guarding the binary_tree fork against silent drift from amsterdam.

`ethereum.forks.binary_tree` is deliberately a byte-for-byte copy of
`ethereum.forks.amsterdam`, save for the state-provider import swap and
the `PreviousHeader` re-parenting that point binary_tree at amsterdam
instead of amsterdam's own previous fork. Amsterdam keeps evolving on
this branch, so without an executable check the copy would rot
unnoticed. These tests turn both the copy relationship and the fork's
registration with the CLI tooling into invariants that fail loudly,
and by name, the moment either breaks.
"""

import difflib
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from ethereum.fork_criteria import Unscheduled
from ethereum.forks import amsterdam, binary_tree
from ethereum_spec_tools.evm_tools.utils import (
    get_supported_forks,
    resolve_fork,
)

assert amsterdam.__file__ is not None
assert binary_tree.__file__ is not None
AMSTERDAM_DIR = Path(amsterdam.__file__).parent
BINARY_TREE_DIR = Path(binary_tree.__file__).parent

# `__init__.py` differs wholesale (docstring plus the `FORK_CRITERIA`
# ordinal); it is whitelisted rather than diffed line by line.
WHOLESALE_WHITELISTED_FILE = "__init__.py"

# The only lines allowed to differ between a binary_tree module and its
# amsterdam counterpart, after normalization, keyed by path relative to
# each fork's package directory. Every (amsterdam, binary_tree) pair
# here must show up as a removed/added line in that file's diff, and no
# other changed line is tolerated: this dict *is* the pinned contract.
ALLOWED_DELTAS: Dict[str, List[Tuple[str, str]]] = {
    "fork.py": [
        (
            "from ethereum.forks.bpo5.blocks import Header as PreviousHeader",
            "from ethereum.forks.amsterdam.blocks import Header as "
            "PreviousHeader",
        ),
        (
            "from ethereum.state_mpt import State, apply_changes_to_state",
            "from ethereum.state_pbt import State, apply_changes_to_state",
        ),
    ],
    "vm/gas.py": [
        (
            "from ethereum.forks.bpo5.blocks import Header as PreviousHeader",
            "from ethereum.forks.amsterdam.blocks import Header as "
            "PreviousHeader",
        ),
    ],
}


def _normalize(binary_tree_text: str) -> str:
    """
    Rewrite binary_tree-specific spellings to their amsterdam form.

    Diffing the two trees turned up exactly two spelling differences
    that are not real logic changes: the fork's dotted module path,
    which as a substring also covers the bare `binary_tree` word used
    in a couple of module docstrings, and the "Binary Tree" title-cased
    two-word form used in `utils/hexadecimal.py`. Both are pinned here
    explicitly; anything they fail to reconcile surfaces as a genuine
    diff to the caller.
    """
    text = binary_tree_text.replace("Binary Tree", "Amsterdam")
    return text.replace("binary_tree", "amsterdam")


def _relative_py_paths(directory: Path) -> Set[str]:
    """
    Return every `*.py` file under `directory`, as relative POSIX paths.
    """
    return {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*.py")
    }


# A unified-diff hunk header, e.g. `@@ -12 +12,2 @@`. No content line
# can ever match this: every content line keeps its own leading
# ` `/`-`/`+` marker, so the earliest a content line's text could
# start contributing to a match is column 1, not column 0.
_HUNK_HEADER_RE = re.compile(r"^@@ -[\d,]+ \+[\d,]+ @@")


def _diff_lines(
    amsterdam_text: str, normalized_binary_tree_text: str
) -> Tuple[Set[str], Set[str]]:
    """
    Return the (removed, added) lines of a zero-context unified diff.

    `removed` holds every line present only in `amsterdam_text`; `added`
    holds every line present only in `normalized_binary_tree_text`.
    Lines common to both never appear in either set, regardless of how
    far apart they sit in the file.

    The `---`/`+++` file-header pair is dropped positionally: when
    `difflib.unified_diff` yields anything at all, those are always
    exactly its first two entries. They are deliberately not
    recognized by sniffing their `---`/`+++` text, because a genuinely
    changed line can produce that same text once its own `-`/`+`
    diff marker is prepended: e.g. a removed line that itself reads
    `------------` (a numpydoc section underline, common in this
    codebase's docstrings) becomes the diff line `-------------`,
    which a naive `startswith(("---", ...))` filter would misfile as
    a header and silently drop. Hunk headers are recognized by their
    full `@@ -a,b +c,d @@` shape (`_HUNK_HEADER_RE`) rather than a
    bare `@@` prefix, for the same reason.
    """
    diff = list(
        difflib.unified_diff(
            amsterdam_text.splitlines(),
            normalized_binary_tree_text.splitlines(),
            n=0,
            lineterm="",
        )
    )
    removed: Set[str] = set()
    added: Set[str] = set()
    for line in diff[2:]:
        if _HUNK_HEADER_RE.match(line):
            continue
        if line.startswith("-"):
            removed.add(line[1:])
        elif line.startswith("+"):
            added.add(line[1:])
    return removed, added


def test_diff_lines_reports_removed_line_starting_with_dashes() -> None:
    """
    A removed line that itself starts with `--` is still reported.

    Regression test: the header/hunk filter used to sniff line
    content (`startswith(("---", "+++", "@@"))`) instead of position,
    so a removed line like `------------` became the diff line
    `-------------` and was misfiled as a file header and dropped.
    """
    amsterdam_text = "one\n------------\ntwo\n"
    binary_tree_text = "one\ntwo\n"

    removed, added = _diff_lines(amsterdam_text, binary_tree_text)

    assert removed == {"------------"}
    assert added == set()


def test_diff_lines_reports_added_line_starting_with_pluses() -> None:
    """
    An added line that itself starts with `++` is still reported.

    Same regression as the dashes case above, mirrored for the
    `+++` file-header text: an added `++++++++++++` line becomes the
    diff line `+++++++++++++`, which must not be mistaken for the
    `+++` to-file header.
    """
    amsterdam_text = "one\ntwo\n"
    binary_tree_text = "one\n++++++++++++\ntwo\n"

    removed, added = _diff_lines(amsterdam_text, binary_tree_text)

    assert removed == set()
    assert added == {"++++++++++++"}


def _apply_allowed_deltas(amsterdam_text: str, relative_path: str) -> str:
    """
    Rewrite `amsterdam_text`'s pinned lines to their binary_tree form.

    Applies every `ALLOWED_DELTAS` substitution registered for
    `relative_path`, in file order, unconditionally -- regardless of
    whether the "old" text is still there. That is what makes a
    vanished delta still fail the caller's exact string comparison: if
    someone quietly reverts binary_tree's copy of a pinned line back to
    amsterdam's own text, this function still produces the substituted
    ("new") text on the amsterdam side, so the two no longer match.
    """
    patched = amsterdam_text
    for old, new in ALLOWED_DELTAS.get(relative_path, []):
        patched = patched.replace(old, new)
    return patched


def test_binary_tree_fork_matches_amsterdam_modulo_known_deltas() -> None:
    """
    binary_tree's `*.py` files match amsterdam's modulo pinned deltas.

    Every `*.py` file under the two fork packages must exist on both
    sides. Patching amsterdam's text with `ALLOWED_DELTAS`'
    substitutions (or, for `__init__.py`, merely requiring the
    binary_tree copy still contain `FORK_CRITERIA`) and normalizing
    binary_tree's spelling must then make the two texts compare EQUAL
    as whole strings. This is a stronger check than a removed/added
    line-SET diff: reordering two statements, or duplicating a line in
    only one copy, changes no set membership and would slip through a
    set comparison, but it does change the string, so this guard still
    catches it. Any remaining difference is unreviewed drift; the
    assertion message names the file and the offending line(s), built
    from `_diff_lines` purely for a readable message -- it plays no
    part in the pass/fail decision. Deltas are applied to amsterdam's
    text unconditionally (see `_apply_allowed_deltas`), so a vanished
    delta -- binary_tree quietly made to match amsterdam instead of
    the pinned divergence -- still produces a text mismatch and fails
    the guard too.
    """
    amsterdam_paths = _relative_py_paths(AMSTERDAM_DIR)
    binary_tree_paths = _relative_py_paths(BINARY_TREE_DIR)
    assert binary_tree_paths == amsterdam_paths, (
        "binary_tree and amsterdam forks contain different sets of "
        "*.py files.\n"
        f"Only in amsterdam: "
        f"{sorted(amsterdam_paths - binary_tree_paths)}\n"
        f"Only in binary_tree: "
        f"{sorted(binary_tree_paths - amsterdam_paths)}"
    )

    problems: List[str] = []
    for relative_path in sorted(amsterdam_paths):
        binary_tree_text = (BINARY_TREE_DIR / relative_path).read_text()

        if relative_path == WHOLESALE_WHITELISTED_FILE:
            if "FORK_CRITERIA" not in binary_tree_text:
                problems.append(
                    f"{relative_path}: whitelisted wholesale, but its "
                    "binary_tree copy no longer contains "
                    "'FORK_CRITERIA'"
                )
            continue

        amsterdam_text = (AMSTERDAM_DIR / relative_path).read_text()
        normalized_binary_tree_text = _normalize(binary_tree_text)
        patched_amsterdam_text = _apply_allowed_deltas(
            amsterdam_text, relative_path
        )

        if patched_amsterdam_text != normalized_binary_tree_text:
            removed, added = _diff_lines(
                patched_amsterdam_text, normalized_binary_tree_text
            )
            problems.append(
                f"{relative_path}: unreviewed drift from amsterdam "
                "(modulo ALLOWED_DELTAS).\n"
                "    amsterdam-only line(s) (post-substitution): "
                f"{sorted(removed)}\n"
                f"    binary_tree-only line(s): {sorted(added)}"
            )

    assert not problems, "\n\n".join(problems)


def test_binary_tree_fork_is_resolvable_by_tooling() -> None:
    """
    The t8n discovery chain resolves binary_tree to the right State.

    `get_supported_forks` must advertise `"BinaryTree"`, and resolving
    that name through the same tooling the transition tool uses must
    load the binary_tree package, whose `fork.State` comes from
    `ethereum.state_pbt`. Amsterdam is resolved alongside as a contrast
    pin: its `fork.State` must still come from `ethereum.state_mpt`.
    """
    assert "BinaryTree" in get_supported_forks()

    binary_tree_fork = resolve_fork("BinaryTree")
    assert (
        binary_tree_fork.module("fork").State.__module__
        == "ethereum.state_pbt"
    )

    amsterdam_fork = resolve_fork("Amsterdam")
    assert (
        amsterdam_fork.module("fork").State.__module__ == "ethereum.state_mpt"
    )


def _order_index(criteria: Unscheduled) -> int:
    """
    Extract the `order_index` an `Unscheduled` was constructed with.

    `Unscheduled` keeps `order_index` behind a private field; its
    `repr` is the only public surface that exposes the value, so parse
    that instead of reaching into the private attribute.
    """
    match = re.fullmatch(r"Unscheduled\(order_index=(\d+)\)", repr(criteria))
    assert match is not None, f"unexpected Unscheduled repr: {criteria!r}"
    return int(match.group(1))


def test_binary_tree_fork_criteria_follows_amsterdam() -> None:
    """
    binary_tree's `FORK_CRITERIA` orders one past amsterdam's.

    Both forks' `FORK_CRITERIA` must be `Unscheduled`, and binary_tree's
    `order_index` must sit exactly one past amsterdam's, whatever
    amsterdam's happens to be today: the ordering is pinned relative to
    amsterdam, not to a hardcoded absolute value.
    """
    amsterdam_criteria = amsterdam.FORK_CRITERIA
    binary_tree_criteria = binary_tree.FORK_CRITERIA
    assert isinstance(amsterdam_criteria, Unscheduled)
    assert isinstance(binary_tree_criteria, Unscheduled)

    assert _order_index(binary_tree_criteria) == (
        _order_index(amsterdam_criteria) + 1
    )
