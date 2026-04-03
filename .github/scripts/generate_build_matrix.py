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
shared ``fork-ranges`` defined at the top of the config.  Features
using ``--fork`` (single fork) produce a single unsplit entry.

Fork-range builds are **deduplicated** across features that share the
same effective fill configuration (evm-type and fill-params ignoring
``--until``).  Each fork range is built once; the combine step
assembles the right subset into each feature's release tarball.
"""

import json
import re
import sys
from pathlib import Path

import yaml

FEATURE_CONFIG = Path(".github/configs/feature.yaml")

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


def load_config(path: Path) -> dict:
    """Load and return the feature configuration."""
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


def strip_until(fill_params: str) -> str:
    """Remove ``--until=FORK`` or ``--until FORK`` from fill-params."""
    return re.sub(r"--until[=\s]+\S+\s*", "", fill_params).strip()


def effective_key(feature: dict) -> str:
    """
    Return a hashable key for grouping features that can share builds.

    Two features share builds when they have the same evm-type and the
    same fill-params after stripping ``--until``.
    """
    return f"{feature['evm-type']}|{strip_until(feature['fill-params'])}"


def applicable_ranges(fork_ranges: list[dict], until_fork: str) -> list[dict]:
    """
    Return fork ranges whose ``from`` is at or before *until_fork*.

    Clamp the last applicable range's ``until`` to *until_fork* so we
    never fill beyond the feature's declared boundary.
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


def build_matrices(
    config: dict, names: list[str]
) -> tuple[list[dict], list[dict]]:
    """
    Build deduplicated build matrix and per-feature combine matrix.

    Return (build_entries, combine_entries).
    """
    fork_ranges = config.get("fork-ranges", [])
    build: list[dict] = []
    combine: list[dict] = []
    seen_labels: set[str] = set()

    # Group splittable features by effective fill config so features
    # with identical builds share runners.
    groups: dict[str, list[str]] = {}
    unsplit: list[str] = []

    for name in names:
        feature = config[name]
        until = parse_until_fork(feature["fill-params"])
        if until and fork_ranges:
            ranges = applicable_ranges(fork_ranges, until)
            if len(ranges) > 1:
                key = effective_key(feature)
                groups.setdefault(key, []).append(name)
                continue
        unsplit.append(name)

    # Emit deduplicated build entries for each group.
    for _key, group_names in groups.items():
        # Use the first feature as reference for the build step.
        ref = group_names[0]

        # Union of all applicable ranges across features in this group.
        all_ranges: dict[str, dict] = {}
        feature_labels: dict[str, list[str]] = {}
        for name in group_names:
            until = parse_until_fork(config[name]["fill-params"])
            assert until is not None
            ranges = applicable_ranges(fork_ranges, until)
            feature_labels[name] = [r["label"] for r in ranges]
            for r in ranges:
                if r["label"] not in all_ranges:
                    all_ranges[r["label"]] = r

        # Deduplicate: emit each range label only once.
        for r in all_ranges.values():
            if r["label"] not in seen_labels:
                seen_labels.add(r["label"])
                build.append(
                    {
                        "feature": ref,
                        "label": r["label"],
                        "from_fork": r["from"],
                        "until_fork": r["until"],
                    }
                )

        # Combine entries map features to their applicable labels.
        for name in group_names:
            combine.append(
                {
                    "feature": name,
                    "labels": " ".join(feature_labels[name]),
                }
            )

    # Unsplit features get a single build entry each.
    for name in unsplit:
        build.append(
            {
                "feature": name,
                "label": "",
                "from_fork": "",
                "until_fork": "",
            }
        )

    return build, combine


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

    build, combine = build_matrices(config, [name])

    # Extract combine labels for this feature (empty if unsplit).
    labels = combine[0]["labels"] if combine else ""

    print(f"build_matrix={json.dumps(build)}")
    print(f"feature_name={name}")
    print(f"combine_labels={labels}")


if __name__ == "__main__":
    main()
