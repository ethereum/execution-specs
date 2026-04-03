"""Clean CLI command removes generated files and directories."""

import glob
import os
import shutil

import click


@click.command(short_help="Remove all generated files and directories.")
@click.option(
    "--all",
    "all_files",
    is_flag=True,
    help="Remove the virtual environment and .just directories as well.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Simulate the cleanup without removing files.",
)
@click.option("-v", "--verbose", is_flag=True, help="Show verbose output.")
def clean(all_files: bool, dry_run: bool, verbose: bool) -> None:
    """
    Remove all generated files and directories from the repository.

    If `--all` is specified, the virtual environment and .just directory
    will also be removed.

    Args:
        all_files (bool): Remove the virtual environment and .just directory
                          as well.

        dry_run (bool): Simulate the cleanup without removing files.

        verbose (bool): Show verbose output.

    Note: The virtual environment and .just directory are not removed by
    default.

    Example: Cleaning all generated files and directories and show the deleted
    items.

        uv run eest clean --all -v

    Output:

        \b
        🗑️  Deleted: .just
        🗑️  Deleted: .venv
        🗑️  Deleted: src/cli/et/__pycache__
        🗑️  Deleted: src/cli/et/commands/__pycache__
        🗑️  Deleted: src/cli/et/make/__pycache__
        🗑️  Deleted: src/cli/et/make/commands/__pycache__
        ...
        🧹 Cleanup complete!

    """  # noqa: D417, D301
    # List of items to remove can contain files and directories.
    items_to_remove = [
        ".pytest_cache",
        ".mypy_cache",
        "fixtures",
        "build",
        "site",
        "cached_downloads",
        ".pyspelling_en.dict",
    ]

    # glob patterns to remove.
    patterns_to_remove = ["src/**/__pycache__", "tests/**/__pycache__"]

    for pattern in patterns_to_remove:
        matching_files = glob.glob(pattern, recursive=True)
        items_to_remove.extend(matching_files)

    if all_files:
        items_to_remove.extend([".just", ".venv"])

    # Perform dry run or actual deletion
    for item in items_to_remove:
        if os.path.exists(item):
            if dry_run:
                click.echo(f"[🧐 Dry run] File would be deleted: {item}")
            else:
                try:
                    if os.path.isdir(item):
                        shutil.rmtree(item, ignore_errors=False)
                    else:
                        os.remove(item)

                    # Verbose flag: Output the name of the deleted item
                    if verbose:
                        click.echo(f"🗑️  Deleted: {item}")

                except PermissionError:
                    click.echo(f"❌ Permission denied to remove {item}.")
                except Exception as e:
                    click.echo(f"❌ Failed to remove {item}: {e}")

    if not dry_run:
        click.echo("🧹 Cleanup complete!")
