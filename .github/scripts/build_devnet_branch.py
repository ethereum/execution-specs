# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
# ]
# ///
"""Build a devnet branch by merging EIP branches onto a fork base."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from collections.abc import Sequence

import click

EIP_PATTERN = re.compile(r"^[0-9]+(?:\+[0-9]+)*$")
CANONICAL_REMOTE_SUFFIXES = (
    "ethereum/execution-specs",
    "ethereum/execution-specs.git",
)


def run_git(
    args: Sequence[str],
    *,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a git command and optionally capture its output."""
    command = ["git", *args]
    print(f"+ {shlex.join(command)}")
    return subprocess.run(
        command,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def run_command(args: Sequence[str]) -> None:
    """Run a generic subprocess command."""
    print(f"+ {shlex.join(args)}")
    env = None
    if len(args) >= 2 and args[0] == "uv" and args[1] == "run":
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)
    subprocess.run(args, check=True, text=True, env=env)


def run_static_checks_suite() -> None:
    """Run the static checks used for devnet assembly, excluding codespell."""
    commands = [
        ["uv", "run", "ruff", "check"],
        ["uv", "run", "ruff", "format", "--check"],
        ["uv", "run", "mypy"],
        ["uv", "run", "ethereum-spec-lint"],
        ["uv", "lock", "--check"],
    ]
    # Keep local and CI dry-runs deterministic: do not invoke actionlint,
    # pyflakes, or shellcheck from this script, since those are external tools
    # that may or may not be installed in a given environment.
    for command in commands:
        run_command(command)


def parse_eip_numbers(raw_eip_numbers: str) -> list[str]:
    """Parse a comma-separated list of EIP numbers."""
    eip_numbers: list[str] = []
    for raw_eip in raw_eip_numbers.split(","):
        eip = raw_eip.strip()
        if not eip:
            continue
        if EIP_PATTERN.fullmatch(eip) is None:
            raise ValueError(
                f"Invalid EIP number '{eip}'. "
                "Expected digits optionally joined by '+'."
            )
        eip_numbers.append(eip)
    if not eip_numbers:
        raise ValueError("No EIP numbers were provided.")
    return eip_numbers


def ensure_clean_tracked_worktree() -> None:
    """Refuse to rewrite branches when tracked changes are present."""
    result = run_git(
        ["status", "--short", "--untracked-files=no"],
        capture_output=True,
    )
    tracked_changes = [
        line
        for line in result.stdout.splitlines()
        if line.strip() and not line[3:].startswith(".github/")
    ]
    if tracked_changes:
        raise RuntimeError(
            "Tracked changes outside .github/ are present in the worktree. "
            "Commit, stash, or discard them before building a devnet branch."
        )


def ensure_valid_branch_name(branch: str) -> None:
    """Validate a branch name with git's ref-format checks."""
    run_git(["check-ref-format", "--branch", branch])


def get_git_output(args: Sequence[str]) -> str:
    """Run a git command and return its stdout."""
    result = run_git(args, capture_output=True)
    return result.stdout.strip()


def get_current_branch() -> str | None:
    """Return the current branch name, or None when HEAD is detached."""
    result = run_git(
        ["branch", "--show-current"],
        check=False,
        capture_output=True,
    )
    current_branch = result.stdout.strip()
    return current_branch or None


def merge_in_progress() -> bool:
    """Return True when the repository has an in-progress merge."""
    result = run_git(
        ["rev-parse", "-q", "--verify", "MERGE_HEAD"],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def detect_canonical_remote() -> str:
    """Find the remote pointing to ethereum/execution-specs."""
    remote_names = get_git_output(["remote"]).splitlines()
    matching_remotes: list[str] = []

    for remote_name in remote_names:
        remote_url = get_git_output(["remote", "get-url", remote_name])
        normalized_url = remote_url.rstrip("/")
        if normalized_url.endswith(CANONICAL_REMOTE_SUFFIXES):
            matching_remotes.append(remote_name)

    if not matching_remotes:
        raise RuntimeError(
            "Could not find a git remote for ethereum/execution-specs. "
            "Pass --remote explicitly."
        )

    if len(matching_remotes) > 1:
        matches = ", ".join(sorted(matching_remotes))
        raise RuntimeError(
            "Found multiple git remotes for ethereum/execution-specs: "
            f"{matches}. Pass --remote explicitly."
        )

    selected_remote = matching_remotes[0]
    print(f"Using canonical remote {selected_remote}")
    return selected_remote


def ensure_remote_branch_exists(remote: str, branch: str) -> None:
    """Ensure a remote-tracking branch exists locally after fetch."""
    remote_branch_ref = f"refs/remotes/{remote}/{branch}"
    try:
        run_git(["show-ref", "--verify", "--quiet", remote_branch_ref])
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Missing remote branch {remote}/{branch}."
        ) from error


def local_branch_exists(branch: str) -> bool:
    """Return True if a local branch exists."""
    result = run_git(
        ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        check=False,
    )
    return result.returncode == 0


def resolve_branch_ref(
    *,
    branch: str,
    remote: str,
    use_local_branches: bool,
) -> str:
    """Resolve a branch to either a local branch or a remote-tracking ref."""
    if use_local_branches and local_branch_exists(branch):
        print(f"Using local branch {branch}")
        return branch

    ensure_remote_branch_exists(remote, branch)
    remote_branch_ref = f"{remote}/{branch}"
    print(f"Using remote branch {remote_branch_ref}")
    return remote_branch_ref


def create_devnet_branch(
    devnet_branch: str,
    fork_ref: str,
) -> None:
    """Reset the local devnet branch to the fork base."""
    print(f"Creating {devnet_branch} from {fork_ref}")
    run_git(["checkout", "-B", devnet_branch, fork_ref])


def restore_original_branch(original_branch: str | None) -> None:
    """Switch back to the starting branch when one was recorded."""
    if original_branch is None:
        print(
            "Started from a detached HEAD; "
            "leaving the current checkout in place"
        )
        return

    current_branch = get_current_branch()
    if current_branch == original_branch:
        print(f"Already on original branch {original_branch}")
        return

    print(f"Switching back to original branch {original_branch}")
    run_git(["checkout", original_branch])


def abort_in_progress_merge() -> None:
    """Abort an in-progress merge so the original branch can be restored."""
    if not merge_in_progress():
        return

    print("Aborting in-progress merge before restoring the original branch")
    run_git(["merge", "--abort"])


def merge_eip_branch(
    devnet_branch: str,
    eip_branch: str,
    eip_ref: str,
) -> None:
    """Merge one EIP branch into the current devnet branch."""
    message = f"Merge {eip_branch} into {devnet_branch}"
    print(f"Merging {eip_ref} into {devnet_branch}")
    try:
        run_git(
            [
                "merge",
                "--no-ff",
                "--no-edit",
                "-m",
                message,
                eip_ref,
            ]
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "Merge conflict while building the devnet branch. "
            "Resolve the conflict locally, or run "
            "`git merge --abort` to clean up."
        ) from error


def push_branch(remote: str, devnet_branch: str) -> None:
    """Push the assembled devnet branch to the remote."""
    print(f"Pushing {devnet_branch} to {remote}")
    run_git(["push", "--force-with-lease", remote, devnet_branch])


@click.command()
@click.option(
    "--fork",
    required=True,
    help="Fork name, for example 'amsterdam'.",
)
@click.option(
    "--devnet-name",
    required=True,
    help=("Devnet name suffix, for example 'bal/3' to build devnets/bal/3."),
)
@click.option(
    "--eip-numbers",
    required=True,
    help="Comma-separated EIP numbers, e.g. '8024,7843,7708,7778'.",
)
@click.option(
    "--remote",
    default=None,
    help=(
        "Git remote containing the fork, EIP, and devnet branches. "
        "Defaults to the remote whose URL points to "
        "ethereum/execution-specs."
    ),
)
@click.option(
    "--push",
    is_flag=True,
    default=False,
    help=(
        "Push the assembled devnet branch back to the remote "
        "with --force-with-lease."
    ),
)
@click.option(
    "--run-static-checks",
    is_flag=True,
    default=False,
    help="Run static checks before pushing, excluding codespell.",
)
@click.option(
    "--use-local-branches",
    is_flag=True,
    default=False,
    help=(
        "Prefer existing local fork and EIP branches when present. "
        "Otherwise fall back to the remote."
    ),
)
def main(
    fork: str,
    devnet_name: str,
    eip_numbers: str,
    remote: str | None,
    push: bool,
    run_static_checks: bool,
    use_local_branches: bool,
) -> None:
    """Build a devnet branch from a fork base and EIP branches."""
    devnet_branch = f"devnets/{devnet_name}"
    original_branch: str | None = None
    restore_original_branch_at_exit = False
    build_error: str | None = None
    restore_failed = False

    try:
        original_branch = get_current_branch()
        resolved_remote = remote or detect_canonical_remote()
        parsed_eip_numbers = parse_eip_numbers(eip_numbers)
        fork_branch = f"forks/{fork}"

        ensure_clean_tracked_worktree()
        ensure_valid_branch_name(devnet_branch)
        ensure_valid_branch_name(fork_branch)

        eip_branches = [
            f"eips/{fork}/eip-{eip_number}"
            for eip_number in parsed_eip_numbers
        ]
        for eip_branch in eip_branches:
            ensure_valid_branch_name(eip_branch)

        run_git(["fetch", resolved_remote, "--prune"])

        fork_ref = resolve_branch_ref(
            branch=fork_branch,
            remote=resolved_remote,
            use_local_branches=use_local_branches,
        )
        eip_refs = {
            eip_branch: resolve_branch_ref(
                branch=eip_branch,
                remote=resolved_remote,
                use_local_branches=use_local_branches,
            )
            for eip_branch in eip_branches
        }

        create_devnet_branch(devnet_branch, fork_ref)
        restore_original_branch_at_exit = True

        for eip_branch in eip_branches:
            merge_eip_branch(devnet_branch, eip_branch, eip_refs[eip_branch])

        if run_static_checks:
            print("Running static checks on the assembled devnet branch")
            run_static_checks_suite()

        if push:
            push_branch(resolved_remote, devnet_branch)
    except (
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        build_error = str(error)
        print(f"Error: {build_error}", file=sys.stderr)
    finally:
        if restore_original_branch_at_exit:
            try:
                if build_error is not None:
                    abort_in_progress_merge()
                restore_original_branch(original_branch)
            except subprocess.CalledProcessError as error:
                target = original_branch or "the original branch"
                print(
                    f"Error: Failed to switch back to {target}: {error}",
                    file=sys.stderr,
                )
                restore_failed = True

    if restore_failed:
        raise SystemExit(1)

    if build_error is not None:
        if "merge conflict" in build_error.lower():
            print("THERE WERE MERGE CONFLICTS")
        raise SystemExit(1)

    print(f"Successfully built {devnet_branch}")


if __name__ == "__main__":
    main()
