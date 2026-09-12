#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# ///
"""
Resolve the fill artifact for a manually dispatched image publication.

Read INPUT_COMMIT and GITHUB_REPOSITORY; print run_id and target_sha for
GITHUB_OUTPUT. Reuse completed scheduled fills even if their subsequent
image publication failed. A live combined artifact is required.
"""

import json
import os

from resolve_cached_release import COMMIT_RE, artifact_name, fail, gh_api


def main() -> None:
    """Find the completed nightly fill and print its artifact location."""
    repository = os.environ["GITHUB_REPOSITORY"]
    commit = os.environ["INPUT_COMMIT"]
    if not COMMIT_RE.fullmatch(commit):
        fail("nightly commit must be 7 to 40 lowercase hex characters")

    # Resolve prefixes once so the artifact, tests and framework all name
    # the same full SHA. Filter by it before pagination, including old fills.
    sha = json.loads(gh_api(f"repos/{repository}/commits/{commit}"))["sha"]
    pages = json.loads(
        gh_api(
            f"repos/{repository}/actions/workflows/release_fixtures.yaml"
            f"/runs?event=schedule&status=completed&head_sha={sha}"
            "&per_page=100",
            paginate=True,
        )
    )
    for page in pages:
        for run in page["workflow_runs"]:
            if run["head_sha"] != sha:
                continue
            run_id = run["id"]
            artifact_pages = json.loads(
                gh_api(
                    f"repos/{repository}/actions/runs/{run_id}"
                    "/artifacts?per_page=100",
                    paginate=True,
                )
            )
            if any(
                a["name"] == artifact_name(sha) and not a["expired"]
                for page in artifact_pages
                for a in page["artifacts"]
            ):
                print(f"run_id={run_id}")
                print(f"target_sha={sha}")
                return
    fail(
        f"no completed scheduled fill at {sha} has a live "
        f"{artifact_name(sha)} artifact; rerun the fill before publishing"
    )


if __name__ == "__main__":
    main()
