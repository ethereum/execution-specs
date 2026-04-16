#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Generate build matrices for release fixture workflows.

Read `.github/configs/feature.yaml` and emit JSON build matrices
suitable for ``strategy.matrix`` in GitHub Actions.

Outputs two matrices:
- ``build_matrix``: pytest-split groups for the fill (phase 2) jobs.
- ``pre_alloc_matrix``: fork-range entries for pre-alloc generation,
  because pre-alloc groups must be generated with complete per-fork
  coverage.
"""

import json
import re
import sys
from pathlib import Path

import yaml

FEATURE_CONFIG = Path(".github/configs/feature.yaml")
FORK_RANGES_CONFIG = Path(".github/configs/fork-ranges.yaml")

# Canonical fork ordering used to filter fork ranges per feature.
FORK_ORDER = [
    "Frontier",
    "Homestead",
    "DAOFork",
    "TangerineWhistle",
    "SpuriousDragon",
    "Byzantium",
    "Constantinople",
    "Istanbul",
    "MuirGlacier",
    "Berlin",
    "London",
    "ArrowGlacier",
    "GrayGlacier",
    "Paris",
    "Shanghai",
    "Cancun",
    "Prague",
    "Osaka",
    "BPO1",
    "BPO2",
    "Amsterdam",
]

FORK_INDEX = {name: i for i, name in enumerate(FORK_ORDER)}


def load_config(path: Path) -> dict | list:
    """Load and return a YAML configuration file."""
    with open(path) as f:
        return yaml.safe_load(f)


def parse_until_fork(fill_params: str) -> str | None:
    """
    Extract the ``--until`` value from fill-params.

    Return ``None`` when ``--fork`` is used instead (single-fork
    feature that should not be split).
    """
    if re.search(r"--fork\b", fill_params):
        return None
    m = re.search(r"--until[=\s]+(\S+)", fill_params)
    return m.group(1) if m else None


def applicable_ranges(fork_ranges: list[dict], until_fork: str) -> list[dict]:
    """
    Return fork ranges whose ``from`` is at or before *until_fork*.

    Clamp the last applicable range's ``until`` to *until_fork* so we
    never generate beyond the feature's declared boundary.
    """
    limit = FORK_INDEX[until_fork]
    result = []
    for r in fork_ranges:
        if FORK_INDEX[r["from"]] <= limit:
            entry = dict(r)
            if FORK_INDEX[r["until"]] > limit:
                entry["until"] = until_fork
            result.append(entry)
    return result


def build_matrix(feature: dict, name: str) -> tuple[list[dict], str]:
    """
    Build the pytest-split matrix for fill (phase 2) jobs.

    Return (build_entries, combine_labels).
    """
    splits = feature.get("splits", 0)

    if splits > 1:
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


def pre_alloc_matrix(
    feature: dict,
    name: str,
    fork_ranges: list[dict],
) -> list[dict]:
    """
    Build the fork-range matrix for pre-alloc generation (phase 1).

    Pre-alloc groups must be generated with complete per-fork coverage,
    so they are split by fork range rather than by pytest-split groups.
    Returns an empty list for unsplit features.
    """
    until = parse_until_fork(feature["fill-params"])
    if not until or not fork_ranges:
        return []

    ranges = applicable_ranges(fork_ranges, until)
    if len(ranges) <= 1:
        return []

    return [
        {
            "feature": name,
            "label": r["label"],
            "from_fork": r["from"],
            "until_fork": r["until"],
        }
        for r in ranges
    ]


def main() -> None:
    """Entry point."""
    if len(sys.argv) != 2:
        print(
            "Usage: generate_build_matrix.py <feature>",
            file=sys.stderr,
        )
        sys.exit(1)

    config = load_config(FEATURE_CONFIG)
    fork_ranges = load_config(FORK_RANGES_CONFIG) or []
    name = sys.argv[1]

    if name not in config or not isinstance(config[name], dict):
        print(
            f"Error: feature '{name}' not found in {FEATURE_CONFIG}.",
            file=sys.stderr,
        )
        sys.exit(1)

    build, labels = build_matrix(config[name], name)
    pre_alloc = pre_alloc_matrix(config[name], name, fork_ranges)

    pa_labels = " ".join(e["label"] for e in pre_alloc)

    print(f"build_matrix={json.dumps(build)}")
    print(f"pre_alloc_matrix={json.dumps(pre_alloc)}")
    print(f"pre_alloc_labels={pa_labels}")
    print(f"feature_name={name}")
    print(f"combine_labels={labels}")


if __name__ == "__main__":
    main()
