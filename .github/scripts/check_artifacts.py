# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml",
#     "click",
# ]
# ///
"""
Check which artifacts need building based on commit changes and path filters.

Compares each artifact's branch against cached workflow artifacts to determine
if a rebuild is needed. Outputs a JSON array of artifact names to build.

Usage:
    uv run check_artifacts.py           # Check all artifacts
    uv run check_artifacts.py --force   # Force build all artifacts
"""

import fnmatch
import json
import subprocess

import click
import yaml

CONFIG_FILE = ".github/configs/feature.yaml"
RESERVED_KEYS = {"common_paths"}
WORKFLOW_NAME = "Fixture Builder"


def run_cmd(cmd: list[str], check: bool = True) -> str | None:
    """Run a command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=check
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def load_config() -> dict:
    """Load feature.yaml configuration."""
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)


def get_artifact_names(config: dict) -> list[str]:
    """Get list of enabled artifact names (excluding reserved keys)."""
    return [
        k
        for k in config
        if k not in RESERVED_KEYS and config[k].get("enabled", True)
    ]


def get_current_sha(branch: str) -> str | None:
    """Get current commit SHA for a branch."""
    run_cmd(["git", "fetch", "origin", branch], check=False)
    return run_cmd(["git", "rev-parse", f"origin/{branch}"], check=False)


def get_cached_artifact_sha(artifact_name: str) -> str | None:
    """Get SHA from the latest cached workflow artifact."""
    # List artifacts from the workflow, looking for our artifact pattern
    output = run_cmd(
        [
            "gh",
            "api",
            "/repos/{owner}/{repo}/actions/artifacts",
            "--jq",
            f'.artifacts[] | select(.name | startswith("{artifact_name}-")) | .name',  # noqa: E501
        ],
        check=False,
    )
    if not output:
        return None

    # Get the first (most recent) matching artifact
    for line in output.splitlines():
        if line.startswith(f"{artifact_name}-"):
            # Extract SHA: "stable-abc123..." -> "abc123..."
            return line[len(artifact_name) + 1 :]
    return None


def get_changed_files(from_sha: str, to_sha: str) -> list[str] | None:
    """Get list of changed files between two commits."""
    output = run_cmd(
        ["git", "diff", "--name-only", f"{from_sha}..{to_sha}"], check=False
    )
    if output is None:
        return None
    return output.splitlines() if output else []


def matches_paths(files: list[str], patterns: list[str]) -> bool:
    """Check if any file matches any of the glob patterns."""
    for file in files:
        for pattern in patterns:
            if fnmatch.fnmatch(file, pattern):
                return True
            # Handle ** patterns
            if "**" in pattern:
                regex_pattern = pattern.replace("**", "*")
                if fnmatch.fnmatch(file, regex_pattern):
                    return True
                # Also try matching without the **/ prefix
                if pattern.startswith("**/"):
                    if fnmatch.fnmatch(file, pattern[3:]):
                        return True
    return False


def check_artifact(
    name: str, config: dict, common_paths: list[str], force: bool
) -> tuple[bool, str]:
    """Check if an artifact needs building. Returns (should_build, reason)."""
    if force:
        return True, "force build requested"

    artifact = config[name]
    branch = artifact["branch"]
    test_paths = artifact.get("test_paths", [])
    paths = test_paths + common_paths

    # Get current SHA
    current_sha = get_current_sha(branch)
    if not current_sha:
        return False, f"could not fetch branch {branch}"

    # Get cached artifact SHA
    cached_sha = get_cached_artifact_sha(name)
    if not cached_sha:
        return True, "no cached artifact found"

    # Check if current SHA matches cached SHA
    if current_sha == cached_sha:
        return False, "no new commits"

    # Check path changes
    changed_files = get_changed_files(cached_sha, current_sha)
    if changed_files is None:
        return True, "could not determine changed files"

    if not changed_files:
        return False, "no files changed"

    if matches_paths(changed_files, paths):
        return True, "relevant files changed"

    return False, "no relevant path changes"


@click.command()
@click.option("--force", is_flag=True, help="Force build all artifacts")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def main(force: bool, verbose: bool) -> None:
    """Check which artifacts need building."""
    config = load_config()
    common_paths = config.get("common_paths", [])
    artifacts = get_artifact_names(config)

    to_build = []

    for name in artifacts:
        should_build, reason = check_artifact(
            name, config, common_paths, force
        )

        if verbose:
            status = "BUILD" if should_build else "SKIP"
            click.echo(f"[{status}] {name}: {reason}", err=True)

        if should_build:
            to_build.append(name)

    # Output JSON array
    click.echo(json.dumps(to_build))


if __name__ == "__main__":
    main()
