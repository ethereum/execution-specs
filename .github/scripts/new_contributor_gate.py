#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# ///
"""
Close pull requests and issues from new contributors that skip the rules.

Usage: `new_contributor_gate.py [--pr N | --issue N | --sweep] [--dry-run]`.

New contributors are authors with nothing merged into the repository
yet, going by `author_association` and confirmed by a search, since the
association can lag days behind a merge. Their pull requests must
reference an issue they are assigned to, and they may have at most
`MAX_OPEN_ISSUES` open issues. Anything else is closed with a comment
explaining the rule (see CONTRIBUTING.md). Everyone else is left alone,
and so are bots, items a maintainer reopened and authors listed in
`.github/configs/new-contributor-gate-bypass.txt`.

A pull request event runs the workflow of the pull request's base
branch, so `--sweep` gates the pull requests opened into every other
branch in the last `SWEEP_HOURS` hours from a schedule on the default
branch instead.

Read the event from `GITHUB_EVENT_PATH` (or the item from `--pr` or
`--issue`) and the repository from `GITHUB_REPOSITORY`, and query GitHub
via the `gh` CLI (authenticated by `GH_TOKEN`).
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# `author_association` of an author with nothing merged yet.
NEW_CONTRIBUTOR = ("NONE", "FIRST_TIMER", "FIRST_TIME_CONTRIBUTOR")

CONFIGS = Path(__file__).parent.parent / "configs"
BYPASS = CONFIGS / "new-contributor-gate-bypass.txt"

MAX_OPEN_ISSUES = 2

# The sweep runs every 15 minutes, so this window also covers late runs.
SWEEP_HOURS = 3

# Hidden in every comment the gate posts, so the sweep can tell a pull
# request a maintainer reopened from one the gate has not seen yet.
MARKER = "<!-- new-contributor-gate -->"

# Most issue references looked up per pull request, to bound API calls.
MAX_REFERENCES = 10

# `#N`, `owner/repo#N` or an issue URL. The repository is checked after.
REFERENCE = re.compile(
    r"(?:https://github\.com/(?P<url_repo>[\w.-]+/[\w.-]+)/issues/"
    r"|(?<![\w.-])(?P<repo>[\w.-]+/[\w.-]+)#"
    r"|(?<![\w/])#)"
    r"(?P<number>\d+)\b"
)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

RND_DISCORD = "https://discord.com/invite/qGpsxSA"
BYPASS_HELP = f"""\
If you are an EIP author or part of an EL client or tooling team, message \
us in `#el-testing` on the [Ethereum R&D Discord]({RND_DISCORD}) or on \
the STEEL Discord server to get added to the bypass list."""

PR_MESSAGE = f"""\
Thanks for your interest in contributing, @{{author}}! Our review \
resources are constrained, so first-time contributors need to be assigned \
to an issue before opening a pull request. This pull request was closed \
automatically, and your branch is untouched.

1. Comment on an existing issue, or open a new one, saying in your own \
words what you want to change and why.
2. Wait for a maintainer to assign you.
3. Open a new pull request with `Closes #<issue>` in its description.

{BYPASS_HELP}

See [CONTRIBUTING.md]({{contributing}}) for details.

{MARKER}"""

ISSUE_MESSAGE = f"""\
Thanks for opening this issue, @{{author}}! Our review resources are \
constrained, so contributors with nothing merged yet can have at most \
{{max_issues}} open issues. This issue was closed automatically. Please \
wait for a reply on your earlier issues.

{BYPASS_HELP}

See [CONTRIBUTING.md]({{contributing}}) for details.

{MARKER}"""


def bypassed(path: Path = BYPASS) -> set[str]:
    """Return the lowercase logins listed in the bypass file."""
    lines = path.read_text().splitlines()
    return {line.split("#", 1)[0].strip().lower() for line in lines} - {""}


def is_new_contributor(
    item: dict[str, Any], sender: str, bypass: set[str]
) -> bool:
    """Return whether a new contributor opened or reopened `item`."""
    author = item["user"]
    return (
        item["author_association"] in NEW_CONTRIBUTOR
        and author["type"] != "Bot"
        and author["login"] == sender
        and author["login"].lower() not in bypass
    )


def referenced_issues(body: str | None, repo: str) -> list[int]:
    """Return the numbers `body` references in `repo`, in order."""
    numbers: list[int] = []
    text = HTML_COMMENT.sub("", body or "")
    for match in REFERENCE.finditer(text):
        other = match["url_repo"] or match["repo"]
        if other is not None and other.lower() != repo.lower():
            continue
        number = int(match["number"])
        if number not in numbers:
            numbers.append(number)
    return numbers


def gh(*args: str, check: bool = True) -> str:
    """Return the stdout of `gh <args>`, exiting non-zero on error."""
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"Error: gh {' '.join(args)} failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout if result.returncode == 0 else ""


def assigned_issue(repo: str, pr: dict[str, Any]) -> int | None:
    """Return an issue `pr` references that its author is assigned to."""
    author = pr["user"]["login"].lower()
    for number in referenced_issues(pr["body"], repo)[:MAX_REFERENCES]:
        found = gh("api", f"repos/{repo}/issues/{number}", check=False)
        issue = json.loads(found) if found else {}
        if not issue or "pull_request" in issue:
            continue
        if author in {a["login"].lower() for a in issue["assignees"]}:
            return number
    return None


def has_merged_pr(repo: str, author: str) -> bool:
    """Return whether `author` has a merged pull request in `repo`."""
    query = f"repo:{repo} is:pr is:merged author:{author}"
    count = gh(
        "api",
        "--method",
        "GET",
        "search/issues",
        "-f",
        f"q={query}",
        "-f",
        "per_page=1",
        "--jq",
        ".total_count",
    )
    return int(count or 0) > 0


def earlier_open_issues(repo: str, author: str, number: int) -> list[int]:
    """Return the open issues `author` opened before issue `number`."""
    query = f"creator={author}&state=open&per_page=100"
    output = gh(
        "api", "--paginate", f"repos/{repo}/issues?{query}", "--jq", ".[]"
    )
    items = [json.loads(line) for line in output.splitlines() if line]
    return sorted(
        item["number"]
        for item in items
        if "pull_request" not in item and item["number"] < number
    )


def already_gated(repo: str, number: int) -> bool:
    """Return whether the gate has commented on `number` before."""
    output = gh(
        "api",
        "--paginate",
        f"repos/{repo}/issues/{number}/comments",
        "--jq",
        ".[].body",
    )
    return MARKER in output


def load_item(
    args: argparse.Namespace, repo: str
) -> tuple[dict[str, Any], bool, str]:
    """Return the item to check, whether it is a PR, and who acted."""
    if args.pr is not None or args.issue is not None:
        kind = "pulls" if args.pr is not None else "issues"
        number = args.pr if args.pr is not None else args.issue
        item = json.loads(gh("api", f"repos/{repo}/{kind}/{number}"))
        return item, args.pr is not None, item["user"]["login"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    is_pr = "pull_request" in event
    item = event["pull_request"] if is_pr else event["issue"]
    return item, is_pr, event["sender"]["login"]


def close(repo: str, number: int, message: str, is_pr: bool) -> None:
    """Comment `message` on an issue or pull request and close it."""
    gh(
        "api",
        "--method",
        "POST",
        f"repos/{repo}/issues/{number}/comments",
        "-f",
        f"body={message}",
    )
    reason = [] if is_pr else ["-f", "state_reason=not_planned"]
    gh(
        "api",
        "--method",
        "PATCH",
        f"repos/{repo}/issues/{number}",
        "-f",
        "state=closed",
        *reason,
    )


def gate(
    repo: str,
    item: dict[str, Any],
    is_pr: bool,
    sender: str,
    dry_run: bool,
    swept: bool = False,
) -> None:
    """Close `item` if a new contributor opened it against the rules."""
    number = item["number"]
    contributing = f"https://github.com/{repo}/blob/HEAD/CONTRIBUTING.md"

    if not is_new_contributor(item, sender, bypassed()):
        print(f"#{number}: skipped, {item['author_association']} by {sender}")
        return
    author = item["user"]["login"]
    if has_merged_pr(repo, author):
        print(f"#{number}: skipped, {author} has a merged pull request")
        return
    if swept and already_gated(repo, number):
        print(f"#{number}: skipped, reopened after the gate closed it")
        return
    if is_pr:
        issue = assigned_issue(repo, item)
        if issue is not None:
            print(f"#{number}: author is assigned to #{issue}")
            return
        message = PR_MESSAGE.format(author=author, contributing=contributing)
    else:
        earlier = earlier_open_issues(repo, author, number)
        if len(earlier) < MAX_OPEN_ISSUES:
            print(f"#{number}: {len(earlier)} earlier open issues")
            return
        message = ISSUE_MESSAGE.format(
            author=author,
            max_issues=MAX_OPEN_ISSUES,
            contributing=contributing,
        )

    print(f"#{number}: closing")
    if not dry_run:
        close(repo, number, message, is_pr)


def sweep(repo: str, now: datetime, dry_run: bool) -> None:
    """Gate recent pull requests into branches other than the default."""
    default = json.loads(gh("api", f"repos/{repo}"))["default_branch"]
    since = now - timedelta(hours=SWEEP_HOURS)
    query = "state=open&sort=created&direction=desc&per_page=100"
    output = gh(
        "api", "--paginate", f"repos/{repo}/pulls?{query}", "--jq", ".[]"
    )
    for line in output.splitlines():
        pr = json.loads(line)
        recent = datetime.fromisoformat(pr["created_at"]) >= since
        if recent and pr["base"]["ref"] != default:
            gate(repo, pr, True, pr["user"]["login"], dry_run, swept=True)


def main() -> None:
    """Gate one pull request or issue, or sweep recent pull requests."""
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--pr", type=int, help="pull request number")
    target.add_argument("--issue", type=int, help="issue number")
    target.add_argument(
        "--sweep",
        action="store_true",
        help="gate recent pull requests into other branches",
    )
    parser.add_argument("--dry-run", action="store_true", help="print only")
    args = parser.parse_args()

    repo = os.environ.get("GITHUB_REPOSITORY", "ethereum/execution-specs")
    if args.sweep:
        sweep(repo, datetime.now(UTC), args.dry_run)
        return
    item, is_pr, sender = load_item(args, repo)
    gate(repo, item, is_pr, sender, args.dry_run)


if __name__ == "__main__":
    main()
