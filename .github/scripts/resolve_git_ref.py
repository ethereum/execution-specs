#!/usr/bin/env -S uv run --script
"""Resolve a GitHub repository branch or full commit SHA."""

import re
import subprocess
import sys

FULL_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def resolve_git_ref(repository: str, ref: str) -> str:
    """Return the commit SHA for a branch name or full commit SHA."""
    if not repository:
        raise ValueError("repository is empty")
    if not ref:
        raise ValueError("ref is empty")
    if FULL_COMMIT_RE.fullmatch(ref):
        return ref.lower()

    branch_ref = ref if ref.startswith("refs/heads/") else f"refs/heads/{ref}"
    result = subprocess.run(
        [
            "git",
            "ls-remote",
            "--exit-code",
            f"https://github.com/{repository}.git",
            branch_ref,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(
            f"could not resolve branch '{ref}' in repository '{repository}'"
        )

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(
            f"branch '{ref}' in repository '{repository}' resolved to "
            f"{len(lines)} commits"
        )
    sha = lines[0].split(maxsplit=1)[0]
    if not FULL_COMMIT_RE.fullmatch(sha):
        raise ValueError(
            f"branch '{ref}' in repository '{repository}' returned an "
            "invalid commit SHA"
        )
    return sha.lower()


def main() -> None:
    """Resolve the command-line repository and ref."""
    if len(sys.argv) != 3:
        print(
            "Usage: resolve_git_ref.py <owner/repository> <branch-or-sha>",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        print(resolve_git_ref(sys.argv[1], sys.argv[2]))
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
