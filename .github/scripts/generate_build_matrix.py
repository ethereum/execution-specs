#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Validate release inputs and generate the build matrix for release
fixture workflows.

Usage: `generate_build_matrix.py <feature> <version> [branch] [evm]`.

First validate the dispatch inputs (see `validate_inputs`), then read
`.github/configs/feature.yaml` and emit a flat JSON build matrix suitable
for `strategy.matrix` in GitHub Actions.

Features whose `fill-params` contain `--until` are split across the
shared fork ranges defined in `.github/configs/fork-ranges.yaml`.
Features using `--fork` (single fork) produce a single unsplit entry.
"""

import json
import re
import sys
from pathlib import Path
from typing import NoReturn

import yaml

FEATURE_CONFIG = Path(".github/configs/feature.yaml")
FORK_RANGES_CONFIG = Path(".github/configs/fork-ranges.yaml")
EVM_CONFIG = Path(".github/configs/evm.yaml")

VERSION_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")

# Devnet release branches follow `devnets/<feat-or-fork>/<n>`, e.g.
# `devnets/bal/7` or `devnets/glamsterdam/6`; `<n>` is the devnet number.
DEVNET_BRANCH_RE = re.compile(r"^devnets/[^/]+/([0-9]+)$")

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
    "BPO3",
    "BPO4",
    "BPO5",
    "Amsterdam",
    "Bogota",
]

FORK_INDEX = {name: i for i, name in enumerate(FORK_ORDER)}


def load_config(path: Path) -> dict:
    """Load and return the feature configuration."""
    with open(path) as f:
        return yaml.safe_load(f)


def fail(message: str) -> NoReturn:
    """Print an error to stderr and exit non-zero."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def validate_inputs(feature: str, version: str, branch: str, evm: str) -> None:
    """
    Validate the release dispatch inputs before building a matrix.

    Centralize the feature/version/evm checks here so they are
    unit-testable rather than living as inline bash in the release
    workflow.

    For `<feat>-devnet` releases the major version (`X` of `vX.Y.Z`)
    must equal the devnet number encoded in the release branch, so a
    `bal-devnet` release from `devnets/bal/7` must be tagged `v7.*.*`.
    """
    if not feature:
        fail("feature name is empty")
    if not VERSION_RE.match(version):
        fail(f"version '{version}' must match vX.Y.Z (e.g. v20.0.0)")

    # An `evm` override must name a key in evm.yaml.
    if evm and evm not in load_config(EVM_CONFIG):
        fail(f"evm '{evm}' is not a key in {EVM_CONFIG}")

    # A bare `devnet` has no friendly `<feat>-` prefix to tag with.
    if feature in ("devnet", "-devnet"):
        fail("devnet releases require a <feat>- prefix, e.g. bal-devnet")

    # `<feat>-devnet-<n>`: the devnet index belongs in the version (X of
    # vX.Y.Z), not in the feature name.
    if "-devnet-" in feature:
        suggested_feature, _, suggested_index = feature.rpartition("-")
        fail(
            "devnet index must go in 'version', not the feature name; "
            f"did you mean feature={suggested_feature} "
            f"version=v{suggested_index}.0.0?"
        )

    if feature.endswith("-devnet"):
        if not branch:
            fail(
                "devnet releases require a 'branch' input, "
                "e.g. branch=devnets/bal/7"
            )
        match = DEVNET_BRANCH_RE.match(branch)
        if not match:
            fail(
                f"could not parse a devnet number from branch '{branch}' "
                "(expected devnets/<feat>/<n>, e.g. devnets/bal/7)"
            )
        devnet_number = int(match.group(1))
        major = int(version.lstrip("v").split(".")[0])
        if major != devnet_number:
            minor_patch = version.split(".", 1)[1]
            fail(
                f"version major (v{major}) must equal the devnet number "
                f"({devnet_number}) from branch '{branch}'; "
                f"did you mean version=v{devnet_number}.{minor_patch}?"
            )


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
    """Validate the inputs and print the build matrix to stdout."""
    args = sys.argv[1:]
    if len(args) < 2:
        print(
            "Usage: generate_build_matrix.py "
            "<feature> <version> [branch] [evm]",
            file=sys.stderr,
        )
        sys.exit(1)

    name = args[0]
    version = args[1]
    branch = args[2] if len(args) > 2 else ""
    evm = args[3] if len(args) > 3 else ""

    validate_inputs(name, version, branch, evm)

    config = load_config(FEATURE_CONFIG)
    fork_ranges = load_config(FORK_RANGES_CONFIG) or []

    # `<feat>-devnet` releases (e.g. bal-devnet) share the `devnet` entry,
    # while keeping their friendly name in the matrix and artifact outputs.
    lookup = (
        "devnet" if name.endswith("-devnet") and "devnet" in config else name
    )

    if lookup not in config or not isinstance(config[lookup], dict):
        print(
            f"Error: feature '{lookup}' not found in {FEATURE_CONFIG}.",
            file=sys.stderr,
        )
        sys.exit(1)

    build, labels = build_matrix(config[lookup], name, fork_ranges)

    print(f"build_matrix={json.dumps(build)}")
    print(f"feature_name={name}")
    print(f"combine_labels={labels}")


if __name__ == "__main__":
    main()
