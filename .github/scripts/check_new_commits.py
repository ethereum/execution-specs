#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# ///
"""
Decide whether a scheduled nightly fill has new commits to fill.

Usage: `check_new_commits.py` (all inputs come from the environment).

Compare the current commit against the head SHA of the last scheduled
run of the release workflow that actually filled: the newest successful
*scheduled* run that uploaded artifacts. A quiet nightly skips its
build jobs yet still concludes as a successful run, so plain success is
no evidence of a fill. Anchoring on real fills means a nightly that
fails or skips keeps re-running until a fill goes green and no commit
slips through unfilled; filtering on scheduled runs means manual
releases never advance the nightly baseline. Manual
(`workflow_dispatch`) runs always run.

A quiet stretch with no new commits still refreshes: once the last
fill is `REFRESH_AGE` old -- or its artifact is no longer live -- the
nightly re-runs anyway, so a live artifact always exists within the
workflow's five-day retention and the release pipeline keeps getting
exercised.

Read `GITHUB_EVENT_NAME`, `GITHUB_REPOSITORY` and `GITHUB_SHA` from the
environment and query the GitHub API via the `gh` CLI (authenticated by
`GH_TOKEN`). Print `run=true|false` to stdout for `$GITHUB_OUTPUT` and
append the new-commit list (or a skip notice) to the
`$GITHUB_STEP_SUMMARY` file.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

WORKFLOW_FILE = "release_fixtures.yaml"

# Re-run a quiet nightly once the last successful fill is this old, so
# a fresh artifact is uploaded before the previous one lapses (the
# workflow retains scheduled tarballs for five days).
REFRESH_AGE = timedelta(days=4)


def gh_api(path: str) -> str:
    """Return the stdout of `gh api <path>`, exiting non-zero on error."""
    result = subprocess.run(
        ["gh", "api", path], capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error: gh api {path} failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


def last_real_nightly(repository: str) -> tuple[str, str, bool]:
    """
    Return the head SHA, creation time and artifact liveness of the
    last scheduled run that actually filled.

    A skipped nightly still concludes as a successful scheduled run,
    so taking the newest success as the baseline would let skip-runs
    keep resetting the refresh clock while the last real artifact
    quietly expires. Walk the recent successful scheduled runs and
    take the newest one that uploaded artifacts, reporting whether any
    of them is still live. Return empty strings when none exists yet.
    """
    runs = json.loads(
        gh_api(
            f"repos/{repository}/actions/workflows/{WORKFLOW_FILE}"
            "/runs?status=success&event=schedule&per_page=10"
        )
    )["workflow_runs"]
    for run in runs:
        artifacts = json.loads(
            gh_api(f"repos/{repository}/actions/runs/{run['id']}/artifacts")
        )["artifacts"]
        if artifacts:
            live = any(not a["expired"] for a in artifacts)
            return str(run["head_sha"]), str(run["created_at"]), live
    return "", "", False


def is_stale(created_at: str) -> bool:
    """Return whether a run created at *created_at* is due a refresh."""
    created = datetime.fromisoformat(created_at)
    return datetime.now(timezone.utc) - created >= REFRESH_AGE


def commits_since(repository: str, last_sha: str, head_sha: str) -> list[str]:
    """Return `- <sha> <subject>` lines for commits after *last_sha*."""
    compare = json.loads(
        gh_api(f"repos/{repository}/compare/{last_sha}...{head_sha}")
    )
    return [
        f"- {c['sha'][:7]} {(c['commit']['message'].splitlines() or [''])[0]}"
        for c in compare["commits"]
    ]


def append_summary(text: str) -> None:
    """Append *text* to the GitHub step summary, or stderr if unset."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write(text + "\n")
    else:
        print(text, file=sys.stderr)


def main() -> None:
    """Print `run=true|false` and write the step summary."""
    if os.environ["GITHUB_EVENT_NAME"] != "schedule":
        # Manual releases always run.
        print("run=true")
        return

    repository = os.environ["GITHUB_REPOSITORY"]
    head_sha = os.environ["GITHUB_SHA"]

    last_sha, last_created, artifact_live = last_real_nightly(repository)
    if last_sha:
        commits = commits_since(repository, last_sha, head_sha)
    else:
        # No prior successful nightly recorded; fill to get a baseline.
        commits = ["- (no previous successful nightly fill found)"]

    if commits:
        print("run=true")
        append_summary(
            "### Commits since last successful nightly fill\n"
            + "\n".join(commits)
        )
    elif not artifact_live:
        print("run=true")
        append_summary(
            "No new commits, but no live fixture artifact exists; refilling."
        )
    elif is_stale(last_created):
        print("run=true")
        append_summary(
            "No new commits, but the last nightly fill is older than "
            f"{REFRESH_AGE.days} days; refreshing before its artifact "
            "retention lapses."
        )
    else:
        print("run=false")
        append_summary(
            "No new commits since the last successful nightly fill; skipping."
        )


if __name__ == "__main__":
    main()
