#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# ///
"""
Decide whether a scheduled nightly fill has new commits to fill.

Usage: `check_new_commits.py` (all inputs come from the environment).

Compare the current commit against the head SHA of the last successful
*scheduled* run of the release workflow. Using the last success (rather
than a fixed time window) means a nightly that fails or is skipped
keeps re-running until it goes green, and no commit slips through
unfilled; filtering on scheduled runs means manual releases never
advance the nightly baseline. Manual (`workflow_dispatch`) runs always
run.

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

WORKFLOW_FILE = "release_fixtures.yaml"


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


def last_successful_nightly_sha(repository: str) -> str:
    """Return the head SHA of the last successful scheduled run."""
    runs = json.loads(
        gh_api(
            f"repos/{repository}/actions/workflows/{WORKFLOW_FILE}"
            "/runs?status=success&event=schedule&per_page=1"
        )
    )["workflow_runs"]
    return str(runs[0]["head_sha"]) if runs else ""


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

    last_sha = last_successful_nightly_sha(repository)
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
    else:
        print("run=false")
        append_summary(
            "No new commits since the last successful nightly fill; skipping."
        )


if __name__ == "__main__":
    main()
