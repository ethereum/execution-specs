"""`eest images`: names and build plans of the hive simulator docker images."""

import json
from typing import Any

import click

from execution_testing.tools import docker_images


@click.group(
    short_help="Names and build plans of the hive simulator docker images."
)
def images() -> None:
    """
    Names and build plans of the docker images of the hive simulators.

    The images and their tags are described in docs/running_tests/hive/images/.
    """


@images.command(name="branch-tag")
@click.argument("branch")
def branch_tag(branch: str) -> None:
    """Print the image tag of BRANCH, e.g. glamsterdam-devnet-8."""
    click.echo(docker_images.branch_tag(branch))


@images.command(name="release-branch")
@click.argument("release_tag")
@click.option(
    "--default-branch",
    required=True,
    help="Default branch; the main line's releases are cut from it.",
)
def release_branch(release_tag: str, default_branch: str) -> None:
    """Print the branch RELEASE_TAG was cut from, e.g. devnets/bal/7."""
    branch = docker_images.branch_for_release(release_tag, default_branch)
    if branch is None:
        raise click.ClickException(
            f"release {release_tag!r} is not tied to a branch"
        )
    click.echo(branch)


@images.command()
@click.option(
    "--branch",
    default=None,
    help=(
        "Branch the images are built from. Required for a push; for a "
        "release it is inferred from the tag and checked when given."
    ),
)
@click.option(
    "--sha",
    required=True,
    help="Commit the images are built from; for a nightly, the fill commit.",
)
@click.option(
    "--default-branch",
    required=True,
    help="Default branch; it owns the main line and the `latest` tags.",
)
@click.option(
    "--release",
    "release_tag",
    default=None,
    help=(
        "Release to build the fixture, tests and simulator images for, e.g. "
        "tests-glamsterdam-devnet@v8.1.4. Without it and --nightly, the "
        "branch's channel owner is rebuilt for a push."
    ),
)
@click.option(
    "--nightly",
    is_flag=True,
    help="Plan a nightly fill: every image at --sha under the nightly tags.",
)
@click.option(
    "--repository",
    default=docker_images.DEFAULT_REPOSITORY,
    show_default=True,
    help="GitHub repository publishing the images.",
)
@click.option(
    "--release-repository",
    default=None,
    help=(
        "Repository holding the releases when it is not the publishing "
        "one; releases are not forked."
    ),
)
@click.option(
    "--resolve-commits",
    is_flag=True,
    help="Resolve the planned release's commit from its tag with git.",
)
@click.option(
    "--github",
    is_flag=True,
    help="Join tag lists into space-separated strings for GitHub Actions.",
)
def plan(
    branch: str | None,
    sha: str,
    default_branch: str,
    release_tag: str | None,
    nightly: bool,
    repository: str,
    release_repository: str | None,
    resolve_commits: bool,
    github: bool,
) -> None:
    """Print, as JSON, what a publishing run builds and how it tags it."""
    release_repo = release_repository or repository
    try:
        result = docker_images.plan(
            branch=branch,
            sha=sha,
            default_branch=default_branch,
            repository=repository,
            release_repository=release_repository,
            release_tag=release_tag,
            nightly=nightly,
            resolve_commit=(
                (lambda tag: docker_images.git_tag_commit(release_repo, tag))
                if resolve_commits
                else None
            ),
        )
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    if github:
        _join_tags(result["base"])
        for key in ("fixtures", "tests"):
            if result[key] is not None:
                _join_tags(result[key])
        for image in result["images"]:
            _join_tags(image)
    click.echo(json.dumps(result))


def _join_tags(entry: dict[str, Any]) -> None:
    entry["tags"] = " ".join(entry["tags"])
