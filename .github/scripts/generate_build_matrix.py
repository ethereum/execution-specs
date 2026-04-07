#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Generate the build matrix for release fixture workflows.

Read `.github/configs/feature.yaml` and emit a flat JSON build matrix
suitable for ``strategy.matrix`` in GitHub Actions.

Features with a ``splits`` property are distributed across N pytest-split
groups.  Features without ``splits`` (single-fork) produce a single
unsplit entry.
"""

import json
import re
import sys
from pathlib import Path

import yaml

FEATURE_CONFIG = Path(".github/configs/feature.yaml")


def load_config(path: Path) -> dict:
    """Load and return the feature configuration."""
    with open(path) as f:
        return yaml.safe_load(f)


def is_multi_fork(fill_params: str) -> bool:
    """Return True when fill-params uses ``--until`` (multi-fork feature)."""
    return bool(re.search(r"--until\b", fill_params))


def build_matrix(feature: dict, name: str) -> tuple[list[dict], str]:
    """
    Build the matrix for a single feature.

    Return (build_entries, combine_labels).  Features with ``splits``
    produce one entry per group and a space-separated label string for
    the combine step.  Unsplit features produce a single entry with
    empty labels.
    """
    splits = feature.get("splits", 0)

    if splits > 1 and is_multi_fork(feature["fill-params"]):
        build = [
            {
                "feature": name,
                "label": str(g),
                "splits": splits,
                "group": g,
            }
            for g in range(1, splits + 1)
        ]
        labels = " ".join(str(g) for g in range(1, splits + 1))
        return build, labels

    return [
        {
            "feature": name,
            "label": "",
            "splits": 0,
            "group": 0,
        }
    ], ""


def main() -> None:
    """Entry point."""
    if len(sys.argv) != 2:
        print(
            "Usage: generate_build_matrix.py <feature>",
            file=sys.stderr,
        )
        sys.exit(1)

    config = load_config(FEATURE_CONFIG)
    name = sys.argv[1]

    if name not in config or not isinstance(config[name], dict):
        print(
            f"Error: feature '{name}' not found in {FEATURE_CONFIG}.",
            file=sys.stderr,
        )
        sys.exit(1)

    build, labels = build_matrix(config[name], name)

    print(f"build_matrix={json.dumps(build)}")
    print(f"feature_name={name}")
    print(f"combine_labels={labels}")


if __name__ == "__main__":
    main()
