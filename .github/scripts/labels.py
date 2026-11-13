#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Sync the repository's labels with `.github/configs/labels.yaml`.

Usage: `labels.py [--apply | --check] [--prune] [--repo OWNER/NAME]`.

Without flags, print the changes and make none. `--apply` makes them:
create or update each label, rename the first old label of its `from`
list that exists (keeping its assignments), and merge the other old
labels into it. A merge adds the label to every issue and pull request
that has the old one, closed ones too, before deleting the old label.
`--prune` also deletes the labels the file does not list, so a run
without it deletes only the old labels of `from` lists. `--check` exits
non-zero when the repository does not match the file.

Query GitHub via the `gh` CLI.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn
from urllib.parse import quote

import yaml

CONFIG = Path(__file__).parent.parent / "configs" / "labels.yaml"
KEYS = {"name", "color", "description", "from"}
COLOR = re.compile(r"^[0-9a-f]{6}$")
MAX_DESCRIPTION = 100  # GitHub rejects longer descriptions


@dataclass(frozen=True)
class Label:
    """A label as the file defines it."""

    name: str
    color: str
    description: str
    old: tuple[str, ...] = ()


@dataclass(frozen=True)
class Change:
    """One change to the repository's labels."""

    kind: str  # create, update, rename, merge or delete
    name: str  # the existing label, or the new one for a create
    label: Label | None = None

    def __str__(self) -> str:
        """Describe the change."""
        if self.label is None or self.label.name == self.name:
            return f"{self.kind} {self.name}"
        return f"{self.kind} {self.name} -> {self.label.name}"


def fail(message: str) -> NoReturn:
    """Print an error and exit."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def load_labels(path: Path) -> list[Label]:
    """Read the labels file and check its shape."""
    entries = yaml.safe_load(path.read_text())
    if not isinstance(entries, list):
        fail(f"{path}: expected a list of labels")
    labels = []
    for entry in entries:
        if not isinstance(entry, dict) or not entry.keys() <= KEYS:
            fail(f"{path}: bad entry {entry!r}")
        name = entry.get("name")
        color = entry.get("color")
        description = entry.get("description")
        old = entry.get("from", [])
        if not isinstance(name, str) or not name:
            fail(f"{path}: entry without a name: {entry!r}")
        if not isinstance(color, str) or not COLOR.match(color):
            fail(f"{name}: color must be six lowercase hex digits")
        if not isinstance(description, str) or (
            len(description) > MAX_DESCRIPTION
        ):
            fail(f"{name}: description must be at most 100 characters")
        if not isinstance(old, list) or not all(
            isinstance(o, str) for o in old
        ):
            fail(f"{name}: `from` must be a list of label names")
        labels.append(Label(name, color, description, tuple(old)))
    # GitHub label names are case-insensitive.
    names = [label.name.lower() for label in labels]
    names += [old.lower() for label in labels for old in label.old]
    repeated = sorted({name for name in names if names.count(name) > 1})
    if repeated:
        fail(f"{path}: listed more than once: {', '.join(repeated)}")
    return labels


def plan(
    labels: list[Label], existing: list[dict[str, Any]], prune: bool
) -> list[Change]:
    """
    Return the changes that make the `existing` labels match `labels`.

    Each label is created, renamed or updated before the old labels of
    its `from` list are merged into it, and deletes come last.
    """
    found = {label["name"].lower(): label for label in existing}
    changes = []
    for label in labels:
        current = found.get(label.name.lower())
        olds = [
            found[old.lower()]["name"]
            for old in label.old
            if old.lower() in found
        ]
        if current is None and olds:
            changes.append(Change("rename", olds.pop(0), label))
        elif current is None:
            changes.append(Change("create", label.name, label))
        elif (
            current["name"] != label.name
            or current["color"].lower() != label.color
            or (current["description"] or "") != label.description
        ):
            changes.append(Change("update", current["name"], label))
        changes += [Change("merge", old, label) for old in olds]
    if prune:
        listed = {label.name.lower() for label in labels}
        listed |= {old.lower() for label in labels for old in label.old}
        changes += [
            Change("delete", label["name"])
            for label in existing
            if label["name"].lower() not in listed
        ]
    return changes


def gh(*args: str) -> str:
    """Return the stdout of `gh <args>`, exiting non-zero on error."""
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"gh {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout


def existing_labels(repo: str) -> list[dict[str, Any]]:
    """Return the repository's labels."""
    out = gh(
        "label",
        "list",
        "-R",
        repo,
        "--limit",
        "1000",
        "--json",
        "name,color,description",
    )
    return json.loads(out)


def labeled_items(repo: str, name: str) -> list[int]:
    """Return every issue and pull request, open or closed, with a label."""
    out = gh(
        "api",
        "--paginate",
        f"repos/{repo}/issues?labels={quote(name)}&state=all&per_page=100",
        "--jq",
        ".[].number",
    )
    return [int(number) for number in out.split()]


def apply(repo: str, change: Change, items: list[int]) -> None:
    """Make one change, adding a merged label to `items` first."""
    label = change.label
    if label is None:
        gh("label", "delete", change.name, "-R", repo, "--yes")
        return
    fields = ["--color", label.color, "--description", label.description]
    if change.kind == "create":
        gh("label", "create", label.name, "-R", repo, *fields)
    elif change.kind in ("rename", "update"):
        gh(
            "label",
            "edit",
            change.name,
            "-R",
            repo,
            "--name",
            label.name,
            *fields,
        )
    else:
        for number in items:
            gh(
                "api",
                "--silent",
                "--method",
                "POST",
                f"repos/{repo}/issues/{number}/labels",
                "-f",
                f"labels[]={label.name}",
            )
        gh("label", "delete", change.name, "-R", repo, "--yes")


def main() -> None:
    """Print, check or apply the changes to the repository's labels."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="make changes")
    mode.add_argument(
        "--check", action="store_true", help="fail if anything would change"
    )
    parser.add_argument(
        "--prune", action="store_true", help="delete unlisted labels"
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get(
            "GITHUB_REPOSITORY", "ethereum/execution-specs"
        ),
        help="repository as OWNER/NAME",
    )
    args = parser.parse_args()

    changes = plan(load_labels(CONFIG), existing_labels(args.repo), args.prune)
    for change in changes:
        items = []
        note = ""
        if change.kind == "merge":
            items = labeled_items(args.repo, change.name)
            note = f" ({len(items)} labeled)"
        print(f"{change}{note}")
        if args.apply:
            apply(args.repo, change, items)
    if not changes:
        print(f"The labels of {args.repo} match the file.")
    elif args.check:
        sys.exit(1)
    elif not args.apply:
        print("Dry run. Pass --apply to make these changes.")


if __name__ == "__main__":
    main()
