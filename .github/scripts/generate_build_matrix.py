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

Features whose ``fill-params`` contain ``--until`` are split across the
shared fork ranges defined in `.github/configs/fork-ranges.yaml`.
Features using ``--fork`` (single fork) produce a single unsplit entry.
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
    "Bogota",
]

FORK_INDEX = {name: i for i, name in enumerate(FORK_ORDER)}


def load_config(path: Path) -> dict:
    """Load and return the feature configuration."""
    with open(path) as f:
        return yaml.safe_load(f)


def parse_fork_bounds(fill_params: str) -> tuple[str | None, str | None]:
    """
    Extract the ``--from``/``--until`` forks from fill-params.

    Return ``(None, None)`` when ``--fork`` is used instead (single-fork
    feature that should not be split).  Either element may be ``None``
    when the corresponding flag is absent.
    """
    if re.search(r"--fork\b", fill_params):
        return None, None
    m_from = re.search(r"--from[=\s]+(\S+)", fill_params)
    m_until = re.search(r"--until[=\s]+(\S+)", fill_params)
    return (
        m_from.group(1) if m_from else None,
        m_until.group(1) if m_until else None,
    )


def applicable_ranges(
    fork_ranges: list[dict], from_fork: str | None, until_fork: str
) -> list[dict]:
    """
    Return fork ranges overlapping ``[from_fork, until_fork]``.

    A range is applicable when it intersects the feature's declared
    ``--from``/``--until`` boundary; its ends are clamped so we never
    fill outside that boundary.  When ``from_fork`` is ``None`` the
    lower bound defaults to the earliest fork.
    """
    lower = FORK_INDEX[from_fork] if from_fork else 0
    limit = FORK_INDEX[until_fork]
    result = []
    for r in fork_ranges:
        if FORK_INDEX[r["from"]] <= limit and FORK_INDEX[r["until"]] >= lower:
            entry = dict(r)
            if FORK_INDEX[r["from"]] < lower:
                entry["from"] = from_fork
            if FORK_INDEX[r["until"]] > limit:
                entry["until"] = until_fork
            result.append(entry)
    return result


def build_matrix(
    feature: dict, name: str, fork_ranges: list[dict]
) -> tuple[list[dict], str]:
    """
    Build the matrix for a single feature.

    Return (build_entries, combine_labels).  Split features produce
    one entry per fork range and a space-separated label string for
    the combine step.  Unsplit features produce a single entry with
    empty labels.
    """
    from_fork, until = parse_fork_bounds(feature["fill-params"])
    if until and fork_ranges:
        ranges = applicable_ranges(fork_ranges, from_fork, until)
        if len(ranges) > 1:
            build = [
                {
                    "feature": name,
                    "label": r["label"],
                    "from_fork": r["from"],
                    "until_fork": r["until"],
                }
                for r in ranges
            ]
            labels = " ".join(r["label"] for r in ranges)
            return build, labels

    return [
        {
            "feature": name,
            "label": "",
            "from_fork": "",
            "until_fork": "",
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
    fork_ranges = load_config(FORK_RANGES_CONFIG) or []
    name = sys.argv[1]

    if name not in config or not isinstance(config[name], dict):
        print(
            f"Error: feature '{name}' not found in {FEATURE_CONFIG}.",
            file=sys.stderr,
        )
        sys.exit(1)

    build, labels = build_matrix(config[name], name, fork_ranges)

    print(f"build_matrix={json.dumps(build)}")
    print(f"feature_name={name}")
    print(f"combine_labels={labels}")


if __name__ == "__main__":
    main()
