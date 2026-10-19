#!/usr/bin/env -S uv run --script
"""Check a zkEVM benchmark release request against GitHub state."""

import json
import os
import subprocess
import sys
from typing import Any, NoReturn


def fail(message: str) -> NoReturn:
    """Print an error and stop the request."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def github_api(path: str) -> Any:
    """Return all pages from a GitHub API request."""
    result = subprocess.run(
        ["gh", "api", "--paginate", "--slurp", path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail(f"gh api failed for {path}: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        fail(f"gh api returned invalid JSON for {path}: {error}")


def flatten_pages(response: Any) -> list[dict[str, Any]]:
    """Flatten the page list returned by ``gh api --slurp``."""
    if not isinstance(response, list):
        fail("gh api returned an invalid paginated response")
    items: list[dict[str, Any]] = []
    for page in response:
        if not isinstance(page, list):
            fail("gh api returned an invalid page")
        for item in page:
            if not isinstance(item, dict):
                fail("gh api returned an invalid item")
            items.append(item)
    return items


def matching_refs(repository: str, tag: str) -> list[dict[str, Any]]:
    """Return refs that match *tag*."""
    path = f"repos/{repository}/git/matching-refs/tags/{tag}"
    return flatten_pages(github_api(path))


def check_release(version: str, source_ref: str) -> None:
    """Check the source input and destination release state."""
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not repository:
        fail("GITHUB_REPOSITORY is empty")

    source_tag = f"tests-zkevm@{version}"
    destination_tag = f"tests-zkevm-benchmark@{version}"
    if source_ref != source_tag:
        fail(
            f"source ref must be '{source_tag}' for version '{version}', "
            f"got '{source_ref}'"
        )

    destination_refs = matching_refs(repository, destination_tag)
    if any(
        ref.get("ref") == f"refs/tags/{destination_tag}"
        for ref in destination_refs
    ):
        fail(f"destination tag '{destination_tag}' already exists")

    releases = flatten_pages(
        github_api(f"repos/{repository}/releases?per_page=100")
    )
    if any(release.get("tag_name") == destination_tag for release in releases):
        fail(
            f"destination release or draft '{destination_tag}' already exists"
        )

    print(f"Source tag: {source_tag}")
    print(f"Destination release: {destination_tag}")


def main() -> None:
    """Check the command-line release request."""
    if len(sys.argv) != 3:
        print(
            "Usage: check_zkevm_benchmark_release.py <version> <source-ref>",
            file=sys.stderr,
        )
        sys.exit(1)
    check_release(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
