"""
Test the label sync script and the labels file it reads.

The `gh` CLI is replaced by a fake, so no test touches the network.
"""

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPTS = Path(__file__).parent.parent


def load_script(name: str) -> ModuleType:
    """Import a script as a module."""
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load_script("labels")
bot = load_script("pr_title_and_labels")


def label(name: str, *old: str, color: str = "ffffff") -> Any:
    """Return a label as the file would define it."""
    return m.Label(name, color, f"About {name}.", old)


def existing(name: str, color: str = "ffffff", description: str = "") -> dict:
    """Return a label as `gh label list` reports it."""
    return {
        "name": name,
        "color": color,
        "description": description or f"About {name}.",
    }


def test_labels_file_lists_every_bot_label() -> None:
    """Define every label the bot adds or removes."""
    names = {label.name for label in m.load_labels(m.CONFIG)}
    assert bot.MANAGED_LABELS <= names


def test_labels_file_lists_every_issue_template_label() -> None:
    """Define every label an issue template applies."""
    names = {label.name for label in m.load_labels(m.CONFIG)}
    templates = (SCRIPTS.parent / "ISSUE_TEMPLATE").glob("*.md")
    for template in templates:
        found = re.search(r"^labels: (.*)$", template.read_text(), re.M)
        if found is not None and found[1].strip():
            used = {name.strip() for name in found[1].split(",")}
            assert used <= names, template.name


@pytest.mark.parametrize(
    "text,error",
    [
        ("name: x", "expected a list"),
        ("- {name: x, color: ffffff, description: '', size: 1}", "bad entry"),
        ("- {color: ffffff, description: ''}", "without a name"),
        ("- {name: x, color: FFFFFF, description: ''}", "six lowercase"),
        ("- {name: x, color: ffffff, description: " + "y" * 101 + "}", "100"),
        ("- {name: x, color: ffffff, description: '', from: y}", "list"),
        (
            "- {name: x, color: ffffff, description: ''}\n"
            "- {name: X, color: ffffff, description: ''}",
            "more than once: x",
        ),
        (
            "- {name: x, color: ffffff, description: '', from: [z]}\n"
            "- {name: y, color: ffffff, description: '', from: [Z]}",
            "more than once: z",
        ),
    ],
)
def test_load_labels_rejects_bad_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str, error: str
) -> None:
    """Fail on a malformed entry or a repeated name."""
    path = tmp_path / "labels.yaml"
    path.write_text(text)
    with pytest.raises(SystemExit):
        m.load_labels(path)
    assert error in capsys.readouterr().err


def test_plan_renames_the_first_old_label_and_merges_the_rest() -> None:
    """Keep the first existing old label's assignments by renaming it."""
    labels = [label("spec", "A-gone", "A-spec", "A-tools")]
    current = [existing("A-spec"), existing("A-tools")]
    assert [str(c) for c in m.plan(labels, current, prune=False)] == [
        "rename A-spec -> spec",
        "merge A-tools -> spec",
    ]


def test_plan_merges_into_a_label_that_exists() -> None:
    """Combine the assignments when the new label exists already."""
    labels = [label("spec", "A-spec")]
    current = [existing("spec"), existing("A-spec")]
    assert [str(c) for c in m.plan(labels, current, prune=False)] == [
        "merge A-spec -> spec",
    ]


@pytest.mark.parametrize(
    "current,changes",
    [
        ([], ["create spec"]),
        ([existing("spec")], []),
        ([existing("spec", color="FFFFFF")], []),
        ([existing("Spec")], ["update Spec -> spec"]),
        ([existing("spec", color="000000")], ["update spec"]),
        ([existing("spec", description="Old.")], ["update spec"]),
    ],
)
def test_plan_creates_and_updates(
    current: list[dict], changes: list[str]
) -> None:
    """Create a missing label and update a different one."""
    plan = m.plan([label("spec")], current, prune=False)
    assert [str(change) for change in plan] == changes


def test_plan_deletes_unlisted_labels_only_with_prune() -> None:
    """Delete labels the file does not list only when asked."""
    labels = [label("spec", "A-spec")]
    current = [existing("spec"), existing("A-spec"), existing("P-low")]
    assert [str(c) for c in m.plan(labels, current, prune=True)] == [
        "merge A-spec -> spec",
        "delete P-low",
    ]
    assert "delete P-low" not in map(str, m.plan(labels, current, False))


class FakeGh:
    """Stand in for the `gh` CLI, serving a repository's labels."""

    def __init__(self, labels: list[dict], items: dict[str, list[int]]):
        """Serve these labels and the issues that carry them."""
        self.labels = labels
        self.items = items
        self.writes: list[tuple[str, ...]] = []

    def __call__(self, *args: str) -> str:
        """Answer reads from the fixture and record writes."""
        if args[:2] == ("label", "list"):
            return json.dumps(self.labels)
        if "--paginate" in args:
            name = re.search(r"labels=([^&]+)", args[2])
            assert name is not None
            return "\n".join(map(str, self.items[name[1]]))
        self.writes.append(args)
        return ""


def run_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fake: FakeGh,
    *flags: str,
) -> None:
    """Run the script's `main` against `fake` and a two-label file."""
    path = tmp_path / "labels.yaml"
    path.write_text(
        "- {name: spec, color: ffffff, description: About spec., "
        "from: [A-spec, A-tools]}\n"
        "- {name: good first issue, color: ffffff, "
        "description: About good first issue.}\n"
    )
    monkeypatch.setattr(m, "CONFIG", path)
    monkeypatch.setattr(m, "gh", fake)
    monkeypatch.setattr(sys, "argv", ["labels.py", "--repo", "o/r", *flags])
    m.main()


def migration() -> FakeGh:
    """Return a repository that still has the old labels."""
    return FakeGh(
        [existing("A-spec"), existing("A-tools"), existing("P-low")],
        {"A-tools": [3, 5]},
    )


def test_main_dry_run_makes_no_writes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Print the changes, counting the issues a merge touches."""
    fake = migration()
    run_main(monkeypatch, tmp_path, fake, "--prune")
    assert fake.writes == []
    assert capsys.readouterr().out.splitlines() == [
        "rename A-spec -> spec",
        "merge A-tools -> spec (2 labeled)",
        "create good first issue",
        "delete P-low",
        "Dry run. Pass --apply to make these changes.",
    ]


def test_main_apply_adds_replacements_before_deleting(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Rename, label the merged issues, then delete the old labels."""
    fake = migration()
    run_main(monkeypatch, tmp_path, fake, "--apply", "--prune")
    fields = ("--color", "ffffff", "--description")
    assert fake.writes == [
        (
            "label",
            "edit",
            "A-spec",
            "-R",
            "o/r",
            "--name",
            "spec",
            *fields,
            "About spec.",
        ),
        *(
            (
                "api",
                "--silent",
                "--method",
                "POST",
                f"repos/o/r/issues/{n}/labels",
                "-f",
                "labels[]=spec",
            )
            for n in (3, 5)
        ),
        ("label", "delete", "A-tools", "-R", "o/r", "--yes"),
        (
            "label",
            "create",
            "good first issue",
            "-R",
            "o/r",
            *fields,
            "About good first issue.",
        ),
        ("label", "delete", "P-low", "-R", "o/r", "--yes"),
    ]


def test_main_check_fails_on_a_difference(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Exit non-zero without writing when anything would change."""
    fake = migration()
    with pytest.raises(SystemExit) as exit_info:
        run_main(monkeypatch, tmp_path, fake, "--check")
    assert exit_info.value.code == 1
    assert fake.writes == []


def test_main_check_passes_once_applied(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Report a match when the repository has exactly the file's labels."""
    fake = FakeGh(
        [existing("spec"), existing("good first issue"), existing("stale")],
        {},
    )
    run_main(monkeypatch, tmp_path, fake, "--check")
    assert fake.writes == []
    assert "match the file" in capsys.readouterr().out
