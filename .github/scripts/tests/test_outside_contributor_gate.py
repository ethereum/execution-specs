"""
Test the outside contributor gate script.

The `gh` CLI is replaced by a fake that serves fixtures and records
writes, so no test touches the network.
"""

import importlib.util
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPT = Path(__file__).parent.parent / "outside_contributor_gate.py"


def load_script() -> ModuleType:
    """Import the script as a module."""
    spec = importlib.util.spec_from_file_location(
        "outside_contributor_gate", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load_script()


@pytest.mark.parametrize(
    "body,numbers",
    [
        ("Closes #12", [12]),
        ("Fixes #12 and #12, see #7.", [12, 7]),
        ("Closes o/r#12", [12]),
        ("Closes O/R#12", [12]),
        ("Closes other/repo#12", []),
        ("Closes https://github.com/o/r/issues/12", [12]),
        ("See https://github.com/o/r/pull/12", []),
        ("Closes https://github.com/other/repo/issues/12", []),
        ("<!-- e.g., Fixes #123 -->\nN/A.", []),
        ("Written in C#12", []),
        ("#12abc", []),
        ("", []),
        (None, []),
    ],
)
def test_referenced_issues(body: str | None, numbers: list[int]) -> None:
    """Find same-repository references outside HTML comments."""
    assert m.referenced_issues(body, "o/r") == numbers


@pytest.mark.parametrize(
    "association,user_type,sender,outside",
    [
        ("NONE", "User", "alice", True),
        ("FIRST_TIMER", "User", "alice", True),
        ("FIRST_TIME_CONTRIBUTOR", "User", "alice", True),
        ("CONTRIBUTOR", "User", "alice", True),
        ("MEMBER", "User", "alice", False),
        ("COLLABORATOR", "User", "alice", False),
        ("OWNER", "User", "alice", False),
        ("NONE", "Bot", "alice", False),
        ("NONE", "User", "maintainer", False),
    ],
)
def test_is_outside_contributor(
    association: str, user_type: str, sender: str, outside: bool
) -> None:
    """Gate human outsiders acting on their own items, whatever they merged."""
    item = {
        "author_association": association,
        "user": {"login": "alice", "type": user_type},
    }
    assert m.is_outside_contributor(item, sender, set()) is outside


def test_bypassed_author_is_not_gated() -> None:
    """Skip an author on the bypass list, whatever the login's case."""
    item = {
        "author_association": "NONE",
        "user": {"login": "Bob", "type": "User"},
    }
    assert not m.is_outside_contributor(item, "Bob", {"bob"})


def test_bypassed_skips_comments_and_blank_lines(tmp_path: Path) -> None:
    """Read one login per line, ignoring comments and case."""
    path = tmp_path / "bypass.txt"
    path.write_text("# Trusted.\n\nAlice\nbob  # EIP author\n")
    assert m.bypassed(path) == {"alice", "bob"}


def test_bypass_file_lists_logins() -> None:
    """Keep the real bypass file readable and free of stray text."""
    logins = m.bypassed()
    assert logins
    assert all(login.replace("-", "").isalnum() for login in logins)


def issue(number: int, assignees: list[str]) -> dict[str, Any]:
    """Return an issue fixture with these assignees."""
    return {
        "number": number,
        "assignees": [{"login": login} for login in assignees],
    }


def pull(
    number: int,
    base: str,
    hours_ago: float,
    association: str = "FIRST_TIME_CONTRIBUTOR",
) -> dict[str, Any]:
    """Return an open pull request `alice` opened into `base`."""
    created = datetime.now(UTC) - timedelta(hours=hours_ago)
    return {
        "number": number,
        "body": "",
        "base": {"ref": base},
        "created_at": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "author_association": association,
        "user": {"login": "alice", "type": "User"},
    }


class FakeGh:
    """Stand in for `gh api`, serving fixtures for one repository."""

    def __init__(
        self,
        issues: list[dict[str, Any]] | None = None,
        pulls: list[dict[str, Any]] | None = None,
        comments: dict[int, list[str]] | None = None,
    ):
        """Serve issues, pulls and comments."""
        self.issues = {item["number"]: item for item in issues or []}
        self.pulls = pulls or []
        self.comments = comments or {}
        self.reads: list[tuple[str, ...]] = []
        self.writes: list[tuple[str, ...]] = []

    def __call__(self, path: str, *flags: str, check: bool = True) -> str:
        """Answer reads from the fixtures and record writes."""
        call = (path, *flags)
        if "--method" in flags and flags[flags.index("--method") + 1] != "GET":
            self.writes.append(call)
            return ""
        self.reads.append(call)
        if path == "repos/o/r":
            return json.dumps({"default_branch": "forks/bogota"})
        if path.startswith("repos/o/r/pulls?"):
            return "\n".join(json.dumps(pr) for pr in self.pulls)
        if "/comments" in path:
            number = int(path.split("/")[-2])
            bodies = self.comments.get(number, [])
            return "\n".join(json.dumps({"body": b}) for b in bodies)
        number = int(path.rsplit("/", 1)[1])
        if number in self.issues:
            return json.dumps(self.issues[number])
        assert not check
        return ""


def run_event(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fake: FakeGh,
    event: dict[str, Any],
    *flags: str,
) -> None:
    """Run the script's `main` on `event` against `fake`."""
    path = tmp_path / "event.json"
    path.write_text(json.dumps(event))
    monkeypatch.setattr(m, "gh_api", fake)
    monkeypatch.setattr(m, "bypassed", lambda: {"bob"})
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))
    monkeypatch.setattr(sys, "argv", ["outside_contributor_gate.py", *flags])
    m.main()


def pr_event(
    body: str,
    association: str = "FIRST_TIME_CONTRIBUTOR",
    sender: str = "alice",
) -> dict[str, Any]:
    """Return a pull request event from `alice` with this body."""
    return {
        "action": "opened",
        "sender": {"login": sender},
        "pull_request": {
            "number": 7,
            "body": body,
            "author_association": association,
            "user": {"login": "alice", "type": "User"},
        },
    }


def closed(number: int, message: str) -> list[tuple[str, ...]]:
    """Return the writes that comment `message` and close `number`."""
    return [
        (
            f"repos/o/r/issues/{number}/comments",
            "--method",
            "POST",
            "-f",
            f"body={message}",
        ),
        (
            f"repos/o/r/issues/{number}",
            "--method",
            "PATCH",
            "-f",
            "state=closed",
        ),
    ]


CONTRIBUTING = "https://github.com/o/r/blob/HEAD/CONTRIBUTING.md"
CONTRIBUTING_MD = Path(__file__).parents[3] / "CONTRIBUTING.md"
PR_MESSAGE = m.message(m.PR_MESSAGE, author="alice", contributing=CONTRIBUTING)


def headings(text: str) -> set[str]:
    """Return the anchors GitHub gives the Markdown headings in `text`."""
    found = re.findall(r"^#+ (.+)$", text, re.M)
    return {
        re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")
        for heading in found
    }


def test_messages_link_sections_that_still_exist() -> None:
    """Point every anchor at a heading CONTRIBUTING.md still has."""
    anchors = re.findall(
        rf"{re.escape(CONTRIBUTING)}#([\w-]+)\)",
        PR_MESSAGE,
    )
    assert anchors
    assert set(anchors) <= headings(CONTRIBUTING_MD.read_text())


def test_messages_name_the_author_and_link_the_guide() -> None:
    """Mention the author, link the guide and end with the marker."""
    assert PR_MESSAGE.startswith("Thanks")
    assert "@alice" in PR_MESSAGE
    assert f"{CONTRIBUTING}#" in PR_MESSAGE
    assert m.RND_DISCORD in PR_MESSAGE
    assert PR_MESSAGE.endswith(m.MARKER)
    assert "{" not in PR_MESSAGE


def test_pr_without_reference_is_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Close an outside contributor's pull request that references nothing."""
    fake = FakeGh()
    run_event(monkeypatch, tmp_path, fake, pr_event("Fix a typo."))
    assert fake.writes == closed(7, PR_MESSAGE)


def test_pr_with_assigned_issue_is_left_open(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Leave a pull request alone once its author is assigned."""
    fake = FakeGh(issues=[issue(3, ["bob"]), issue(5, ["Alice"])])
    run_event(monkeypatch, tmp_path, fake, pr_event("See #3. Closes #5."))
    assert fake.writes == []


@pytest.mark.parametrize(
    "issues",
    [
        [issue(5, ["bob"])],
        [issue(5, [])],
        [{**issue(5, ["alice"]), "pull_request": {}}],
        [],
    ],
    ids=["assigned-to-other", "unassigned", "is-a-pr", "missing"],
)
def test_pr_without_assignment_is_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    issues: list[dict[str, Any]],
) -> None:
    """Close a pull request whose reference does not assign its author."""
    fake = FakeGh(issues=issues)
    run_event(monkeypatch, tmp_path, fake, pr_event("Closes #5"))
    assert fake.writes == closed(7, PR_MESSAGE)


def test_pr_references_are_capped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Look up at most `MAX_REFERENCES` issues per pull request."""
    body = " ".join(f"#{n}" for n in range(1, m.MAX_REFERENCES + 5))
    fake = FakeGh()
    run_event(monkeypatch, tmp_path, fake, pr_event(body))
    assert len(fake.reads) == m.MAX_REFERENCES
    assert fake.writes == closed(7, PR_MESSAGE)


@pytest.mark.parametrize(
    "association,sender",
    [("MEMBER", "alice"), ("COLLABORATOR", "alice"), ("NONE", "maintainer")],
)
def test_pr_from_others_is_left_alone(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    association: str,
    sender: str,
) -> None:
    """Skip collaborators, members and pull requests a maintainer reopened."""
    fake = FakeGh()
    event = pr_event("", association=association, sender=sender)
    run_event(monkeypatch, tmp_path, fake, event)
    assert fake.reads == []
    assert fake.writes == []


def test_prior_contributor_is_gated(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Gate an author with merged pull requests like any other outsider."""
    fake = FakeGh()
    event = pr_event("Fix a typo.", association="CONTRIBUTOR")
    run_event(monkeypatch, tmp_path, fake, event)
    assert fake.writes == closed(7, PR_MESSAGE)


def test_dry_run_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Print the decision without commenting or closing."""
    fake = FakeGh()
    run_event(monkeypatch, tmp_path, fake, pr_event(""), "--dry-run")
    assert fake.writes == []


def run_sweep(
    monkeypatch: pytest.MonkeyPatch, fake: FakeGh, *flags: str
) -> None:
    """Run the script's `main` in sweep mode against `fake`."""
    monkeypatch.setattr(m, "gh_api", fake)
    monkeypatch.setattr(m, "bypassed", lambda: {"bob"})
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setattr(
        sys, "argv", ["outside_contributor_gate.py", "--sweep", *flags]
    )
    m.main()


def test_sweep_closes_pr_into_another_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Close a recent outside pull request into any other branch."""
    fake = FakeGh(pulls=[pull(11, "forks/amsterdam", 1)])
    run_sweep(monkeypatch, fake)
    assert fake.writes == closed(11, PR_MESSAGE)


@pytest.mark.parametrize(
    "pr,comments",
    [
        (pull(11, "forks/bogota", 1), {}),
        (pull(11, "forks/amsterdam", m.SWEEP_HOURS + 1), {}),
        (pull(11, "forks/amsterdam", 1, association="COLLABORATOR"), {}),
        (pull(11, "forks/amsterdam", 1), {11: [f"Closed.\n\n{m.MARKER}"]}),
    ],
    ids=["default-branch", "too-old", "collaborator", "reopened"],
)
def test_sweep_leaves_others_alone(
    monkeypatch: pytest.MonkeyPatch,
    pr: dict[str, Any],
    comments: dict[int, list[str]],
) -> None:
    """Skip the default branch, old pull requests, collaborators, reopens."""
    fake = FakeGh(pulls=[pr], comments=comments)
    run_sweep(monkeypatch, fake)
    assert fake.writes == []


def test_sweep_dry_run_writes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Print the sweep's decisions without commenting or closing."""
    fake = FakeGh(pulls=[pull(11, "forks/amsterdam", 1)])
    run_sweep(monkeypatch, fake, "--dry-run")
    assert fake.writes == []
