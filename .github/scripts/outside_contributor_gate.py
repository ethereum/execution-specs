#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# ///
"""
Close pull requests from outside contributors that skip the rules.

Usage: `outside_contributor_gate.py [--pr N | --sweep] [--dry-run]`.

Outside contributors are authors who are neither collaborators nor
members of the organization, going by `author_association`, whatever
they have merged before. Their pull requests must reference an issue
they are assigned to, or they are closed with a comment linking the
rule in CONTRIBUTING.md. Issues are never closed. Collaborators and
members are left alone, and so are bots, pull requests a maintainer
reopened and authors listed in
`.github/configs/outside-contributor-gate-bypass.txt`.

A pull request event runs the workflow of the pull request's base
branch, so `--sweep` gates the pull requests opened into every other
branch in the last `SWEEP_HOURS` hours from a schedule on the default
branch instead.

Read the event from `GITHUB_EVENT_PATH` (or the pull request from
`--pr`) and the repository from `GITHUB_REPOSITORY`, and query GitHub
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
from urllib.parse import urlencode

# `author_association` of collaborators and organization members, the
# authors the gate never checks.
INSIDE = ("OWNER", "MEMBER", "COLLABORATOR")

CONFIGS = Path(__file__).parent.parent / "configs"
BYPASS = CONFIGS / "outside-contributor-gate-bypass.txt"

# The sweep runs hourly, so this window also covers late or dropped runs.
SWEEP_HOURS = 3

# Hidden in every comment the gate posts, so the sweep can tell a pull
# request a maintainer reopened from one the gate has not seen yet.
MARKER = "<!-- outside-contributor-gate -->"

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
us in `#el-testing` on the [Ethereum R&D Discord]({RND_DISCORD}) to get \
added to the bypass list."""

PR_MESSAGE = f"""\
Thanks for your interest in contributing, @{{author}}! Our review \
resources are constrained, so this pull request was closed automatically \
because it does not link an issue assigned to you. Your branch is \
untouched.

See [Outside contributors]({{contributing}}#outside-contributors) \
for the steps to follow. {BYPASS_HELP}"""


def bypassed(path: Path = BYPASS) -> set[str]:
    """Return the lowercase logins listed in the bypass file."""
    lines = path.read_text().splitlines()
    return {line.split("#", 1)[0].strip().lower() for line in lines} - {""}


def message(template: str, **fields: str) -> str:
    """Return `template` filled in and ending with the marker."""
    return f"{template.format(**fields)}\n\n{MARKER}"


def is_outside_contributor(
    pr: dict[str, Any], sender: str, bypass: set[str]
) -> bool:
    """Return whether an outside contributor opened or reopened `pr`."""
    author = pr["user"]
    return (
        pr["author_association"] not in INSIDE
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


def gh_api(path: str, *flags: str, check: bool = True) -> str:
    """Return the stdout of `gh api <path>`, exiting non-zero on error."""
    args = ["api", path, *flags]
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"Error: gh {' '.join(args)} failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout if result.returncode == 0 else ""


def endpoint(path: str, params: dict[str, str]) -> str:
    """Return `path` with `params` as its query string."""
    return f"{path}?{urlencode(params)}" if params else path


def api(path: str, check: bool = True, **params: str) -> Any:
    """Return the JSON at `path`, or `None` if the read failed."""
    output = gh_api(endpoint(path, params), check=check)
    return json.loads(output) if output else None


def api_list(path: str, **params: str) -> list[dict[str, Any]]:
    """
    Return every item at `path`, across pages.

    `--paginate` concatenates one array per page, which is not valid
    JSON, so `--jq` flattens the pages into one object per line.
    """
    params["per_page"] = "100"
    path = endpoint(path, params)
    output = gh_api(path, "--paginate", "--jq", ".[]")
    return [json.loads(line) for line in output.splitlines() if line]


def api_write(method: str, path: str, **fields: str) -> None:
    """Send `fields` to `path` with `method`."""
    flags: list[str] = []
    for key, value in fields.items():
        flags += ["-f", f"{key}={value}"]
    gh_api(path, "--method", method, *flags)


def assigned_issue(repo: str, pr: dict[str, Any]) -> int | None:
    """Return an issue `pr` references that its author is assigned to."""
    author = pr["user"]["login"].lower()
    for number in referenced_issues(pr["body"], repo)[:MAX_REFERENCES]:
        issue = api(f"repos/{repo}/issues/{number}", check=False)
        if not issue or "pull_request" in issue:
            continue
        if author in {a["login"].lower() for a in issue["assignees"]}:
            return number
    return None


def already_gated(repo: str, number: int) -> bool:
    """Return whether the gate has commented on `number` before."""
    path = f"repos/{repo}/issues/{number}/comments"
    return any(MARKER in item["body"] for item in api_list(path))


def load_pr(args: argparse.Namespace, repo: str) -> tuple[dict[str, Any], str]:
    """Return the pull request to check and who acted."""
    if args.pr is not None:
        pr = api(f"repos/{repo}/pulls/{args.pr}")
        return pr, pr["user"]["login"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    return event["pull_request"], event["sender"]["login"]


def close(repo: str, number: int, message: str) -> None:
    """Comment `message` on pull request `number` and close it."""
    api_write("POST", f"repos/{repo}/issues/{number}/comments", body=message)
    api_write("PATCH", f"repos/{repo}/issues/{number}", state="closed")


def violation(repo: str, pr: dict[str, Any]) -> str | None:
    """Return the message to close `pr` with, or `None` to leave it."""
    issue = assigned_issue(repo, pr)
    if issue is not None:
        print(f"#{pr['number']}: author is assigned to #{issue}")
        return None
    contributing = f"https://github.com/{repo}/blob/HEAD/CONTRIBUTING.md"
    author = pr["user"]["login"]
    return message(PR_MESSAGE, author=author, contributing=contributing)


def gate(
    repo: str,
    pr: dict[str, Any],
    sender: str,
    dry_run: bool,
    swept: bool = False,
) -> None:
    """Close `pr` if an outside contributor opened it against the rules."""
    number = pr["number"]
    if not is_outside_contributor(pr, sender, bypassed()):
        print(f"#{number}: skipped, {pr['author_association']} by {sender}")
        return
    if swept and already_gated(repo, number):
        print(f"#{number}: skipped, reopened after the gate closed it")
        return
    comment = violation(repo, pr)
    if comment is None:
        return
    print(f"#{number}: closing")
    if not dry_run:
        close(repo, number, comment)


def sweep(repo: str, now: datetime, dry_run: bool) -> None:
    """Gate recent pull requests into branches other than the default."""
    default = api(f"repos/{repo}")["default_branch"]
    since = now - timedelta(hours=SWEEP_HOURS)
    pulls = api_list(
        f"repos/{repo}/pulls",
        state="open",
        sort="created",
        direction="desc",
    )
    for pr in pulls:
        recent = datetime.fromisoformat(pr["created_at"]) >= since
        if recent and pr["base"]["ref"] != default:
            gate(repo, pr, pr["user"]["login"], dry_run, swept=True)


def main() -> None:
    """Gate one pull request, or sweep recent pull requests."""
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--pr", type=int, help="pull request number")
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
    pr, sender = load_pr(args, repo)
    gate(repo, pr, sender, args.dry_run)


if __name__ == "__main__":
    main()
