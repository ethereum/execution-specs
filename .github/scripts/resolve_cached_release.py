#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# ///
"""
Resolve the nightly fill whose artifact a cached release reuses.

Usage: `resolve_cached_release.py` (all inputs come from the
environment).

Dispatching `release_fixtures.yaml` with the `cached` flag drafts a
`tests@` release from the newest nightly artifact instead of
refilling: the scheduled nightly runs already build the mainnet
`tests` feature into a release-shaped `fixtures_<commit>` artifact.
The `commit` input picks the nightly built at that commit instead of
the newest one. This script validates the request, picks the nightly
run whose artifact the release job downloads, and pins the exact
commit that run built so the release tag lands on it.

Checks performed, failing fast on the first violation:

- The release is for the `tests` feature on the default branch (no
  `branch` input): that is what the nightly fills.
- `INPUT_VERSION` matches `vX.Y.Z` and is greater than the newest
  existing `tests@` tag (releases always move forward; anything
  unusual belongs in a fresh fill).
- The resolved run is a successful *scheduled* run of
  `release_fixtures.yaml` with a live (unexpired) tarball artifact
  named for the run's own commit: the newest one, or with
  `INPUT_COMMIT` (7+ hex characters) the one built at that commit.
  Skip-runs upload no artifacts and expired fills cannot be
  downloaded, so both are passed over.
- The resolved commit contains the newest existing `tests@` release,
  so a cached release never regresses content (re-releasing the same
  commit stays allowed).
- The resolved commit is an ancestor of the current branch head.
  Commits after it are listed in the step summary so the releaser can
  see what the release will NOT contain.

Read `GITHUB_REPOSITORY`, `GITHUB_SHA`, `INPUT_FEATURE`,
`INPUT_BRANCH`, `INPUT_VERSION` and `INPUT_COMMIT` from the
environment and query the
GitHub API via the `gh` CLI (authenticated by `GH_TOKEN`). Print
`run_id`, `target_sha` and `artifact_name` as `key=value` lines for
`$GITHUB_OUTPUT`.
"""

import json
import os
import re
import subprocess
import sys
from typing import NoReturn

WORKFLOW_FILE = "release_fixtures.yaml"

# The combined-tarball artifact a nightly `tests` fill uploads is
# named for the short hash of the built commit; only that artifact is
# ever reused by a cached release.
ARTIFACT_PREFIX = "fixtures"

VERSION_RE = re.compile(r"^v([0-9]+)\.([0-9]+)\.([0-9]+)$")
COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")


def artifact_name(head_sha: str) -> str:
    """Return the tarball artifact name of a nightly built at *head_sha*."""
    return f"{ARTIFACT_PREFIX}_{head_sha[:7]}"


def fail(message: str) -> NoReturn:
    """Print an error to stderr and exit non-zero."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def gh_api(path: str, paginate: bool = False) -> str:
    """
    Return the stdout of `gh api <path>`, exiting non-zero on error.

    With *paginate*, follow the Link header through every page and
    return a JSON array of per-page responses (`--slurp`).
    """
    flags = ["--paginate", "--slurp"] if paginate else []
    result = subprocess.run(
        ["gh", "api", *flags, path], capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error: gh api {path} failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


def append_summary(text: str) -> None:
    """Append *text* to the GitHub step summary, or stderr if unset."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write(text + "\n")
    else:
        print(text, file=sys.stderr)


def parse_version(version: str) -> tuple[int, int, int]:
    """Return the (major, minor, patch) tuple of a `vX.Y.Z` version."""
    m = VERSION_RE.match(version)
    if not m:
        fail(f"version '{version}' must match vX.Y.Z (e.g. v5.0.0)")
    major, minor, patch = (int(g) for g in m.groups())
    return major, minor, patch


def newest_tests_tag(repository: str) -> str:
    """
    Return the newest existing `tests@vX.Y.Z` tag, or "" when none.

    The `tests@` ref prefix cannot match any other feature's tags
    (those are namespaced `tests-<feature>@`), so every match is a
    mainnet tests release.

    The listing is paginated in ref-name order, not version order
    (`tests@v9...` sorts after `tests@v20...`), so every page must be
    fetched before taking the maximum.
    """
    pages = json.loads(
        gh_api(
            f"repos/{repository}/git/matching-refs/tags/tests@",
            paginate=True,
        )
    )
    refs = [ref for page in pages for ref in page]
    tags = [ref["ref"].removeprefix("refs/tags/") for ref in refs]
    versioned = [
        (parse_version(tag.removeprefix("tests@")), tag)
        for tag in tags
        if VERSION_RE.match(tag.removeprefix("tests@"))
    ]
    if not versioned:
        return ""
    return max(versioned)[1]


def has_live_tests_artifact(
    repository: str, run_id: str, head_sha: str
) -> bool:
    """
    Return whether *run_id* has a live tarball artifact.

    The artifact name is derived from the run's own head SHA, so a
    name that does not match the commit it claims to be built from is
    passed over.
    """
    artifacts = json.loads(
        gh_api(f"repos/{repository}/actions/runs/{run_id}/artifacts")
    )["artifacts"]
    name = artifact_name(head_sha)
    return any(a["name"] == name and not a["expired"] for a in artifacts)


def cached_run(repository: str, commit: str) -> tuple[str, str]:
    """
    Return the (run id, head SHA) of the nightly run to reuse.

    Take the newest successful scheduled run with a live artifact, or
    with *commit* the run built at that commit (skip-runs upload no
    artifacts and expired fills cannot be downloaded, so both are
    passed over). On a commit miss, list the reusable nightlies.
    """
    runs = json.loads(
        gh_api(
            f"repos/{repository}/actions/workflows/{WORKFLOW_FILE}"
            "/runs?status=success&event=schedule&per_page=10"
        )
    )["workflow_runs"]
    live: list[str] = []
    for run in runs:
        run_id, head_sha = str(run["id"]), str(run["head_sha"])
        if not has_live_tests_artifact(repository, run_id, head_sha):
            continue
        if not commit or head_sha.startswith(commit):
            return run_id, head_sha
        live.append(head_sha[:7])
    if commit:
        available = ", ".join(live) if live else "none"
        fail(
            f"no nightly with a live artifact was built at {commit} "
            f"(reusable nightlies: {available}); dispatch a fresh fill "
            "instead"
        )
    fail(
        f"no scheduled run of {WORKFLOW_FILE} with a live "
        f"`{ARTIFACT_PREFIX}_<commit>` artifact found; dispatch a fresh "
        "fill instead"
    )


def ensure_not_behind(repository: str, prev_tag: str, target_sha: str) -> None:
    """
    Fail when *target_sha* does not contain the *prev_tag* release.

    A cached release must never regress content: the resolved nightly
    has to be at or after the newest `tests@` tag. Re-releasing the
    identical commit stays allowed.
    """
    compare = json.loads(
        gh_api(f"repos/{repository}/compare/{prev_tag}...{target_sha}")
    )
    if compare["status"] not in ("identical", "ahead"):
        fail(
            f"the resolved nightly ({target_sha}) does not contain the "
            f"newest tests release ({prev_tag}); a cached release must "
            "not regress content"
        )


def commits_after(
    repository: str, target_sha: str, head_sha: str
) -> list[str]:
    """
    Return `- <sha> <subject>` lines for commits after *target_sha*.

    Fail when *target_sha* is not an ancestor of *head_sha*: a nightly
    built from a rewritten or foreign branch must not be released.
    """
    compare = json.loads(
        gh_api(f"repos/{repository}/compare/{target_sha}...{head_sha}")
    )
    if compare["status"] not in ("identical", "ahead"):
        fail(
            f"nightly commit {target_sha} is not an ancestor of "
            f"{head_sha} (compare status: {compare['status']})"
        )
    return [
        f"- {c['sha'][:7]} {(c['commit']['message'].splitlines() or [''])[0]}"
        for c in compare["commits"]
    ]


def main() -> None:
    """Print the resolved run for `$GITHUB_OUTPUT` and the summary."""
    repository = os.environ["GITHUB_REPOSITORY"]
    head_sha = os.environ["GITHUB_SHA"]
    version = os.environ["INPUT_VERSION"]

    if os.environ.get("INPUT_FEATURE") != "tests":
        fail("cached releases are only available for feature=tests")
    if os.environ.get("INPUT_BRANCH"):
        fail(
            "cached releases reuse a default-branch nightly; drop the "
            "`branch` input or dispatch a fresh fill"
        )

    commit = os.environ.get("INPUT_COMMIT", "")
    if commit and not COMMIT_RE.match(commit):
        fail(f"commit '{commit}' must be 7 to 40 lowercase hex characters")

    requested = parse_version(version)
    prev_tag = newest_tests_tag(repository)
    if prev_tag and requested <= parse_version(
        prev_tag.removeprefix("tests@")
    ):
        fail(
            f"version '{version}' must be greater than the newest "
            f"tests release ({prev_tag})"
        )

    run_id, target_sha = cached_run(repository, commit)
    if prev_tag:
        ensure_not_behind(repository, prev_tag, target_sha)
    missing = commits_after(repository, target_sha, head_sha)

    print(f"run_id={run_id}")
    print(f"target_sha={target_sha}")
    print(f"artifact_name={artifact_name(target_sha)}")

    run_url = f"https://github.com/{repository}/actions/runs/{run_id}"
    append_summary(
        f"Reusing nightly fill run [{run_id}]({run_url}) "
        f"(built at `{target_sha}`) for the `tests@{version}` draft."
    )
    if missing:
        append_summary(
            "### Commits NOT included in this release\n"
            + "\n".join(missing)
            + "\n\nDispatch a fresh fill to include them."
        )
    else:
        append_summary(
            "The nightly is up to date with the current branch head."
        )


if __name__ == "__main__":
    main()
