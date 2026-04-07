"""
Check split balance for the grouped least-duration algorithm.

Reads a ``.test_durations`` file and a list of nodeids, simulates a
split, and prints per-runner group counts and estimated durations.

Run via ``uv run python scripts/check_split_balance.py ...``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

import click


class Item(NamedTuple):
    """Minimal item stub with a nodeid attribute."""

    nodeid: str


@click.command()
@click.option(
    "--durations",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to .test_durations JSON file.",
)
@click.option(
    "--nodeids",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to file with one test nodeid per line.",
)
@click.option(
    "--splits",
    required=True,
    type=int,
    help="Number of runners to split across.",
)
def main(durations: Path, nodeids: Path, splits: int) -> None:
    """Simulate a grouped least-duration split and print balance."""
    from execution_testing.pytest_plugins.split.grouped_least_duration import (
        grouped_least_duration,
        grouping_key,
        normalize_durations,
    )

    durations_data = normalize_durations(json.loads(durations.read_text()))
    items = [
        Item(line.strip())
        for line in nodeids.read_text().splitlines()
        if line.strip()
    ]

    click.echo(f"Tests: {len(items)}")
    click.echo(f"Splits: {splits}")

    # Count unique groups
    unique_groups = {grouping_key(item.nodeid) for item in items}
    click.echo(f"Groups: {len(unique_groups)}")
    click.echo()

    groups = grouped_least_duration(
        splits=splits, items=items, durations=durations_data
    )

    runner_durations = []
    for i, group in enumerate(groups, 1):
        group_keys = {grouping_key(item.nodeid) for item in group.selected}
        click.echo(
            f"Runner {i}:  {len(group_keys):>5} groups  "
            f"~{group.duration:>8.1f}s estimated"
        )
        runner_durations.append(group.duration)

    if runner_durations:
        max_d = max(runner_durations)
        min_d = (
            min(d for d in runner_durations if d > 0)
            if any(d > 0 for d in runner_durations)
            else 1.0
        )
        click.echo(f"\nMax/min ratio: {max_d / min_d:.2f}")


if __name__ == "__main__":
    main()
