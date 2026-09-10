#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Validate a manual mainnet `tests@` release against the configured
series.

Usage: `validate_mainnet_release.py` (all inputs come from the
environment).

Maintainers explicitly select the mainnet `X.Y` release series in
`.github/configs/mainnet_fixture_version.yaml`. Major and
consensus-minor releases are manual, and this check keeps them in
lockstep with that configuration when `release_fixtures.yaml` is
dispatched for the `tests` feature:

- A version inside the published series (a manual patch or re-fill)
  must simply be greater than the newest published release.
- A version starting a new series must be exactly the configured
  `vX.Y.0`, and the configuration must be a valid successor of the
  published series (checked by `series_transition`, which also rejects
  a malformed configuration).
- A cached new-series release must use a nightly whose target commit
  already contains that exact configured series. This prevents a
  consensus or fork release from attaching stale pre-change fixtures.
- A version starting a series the configuration does not acknowledge
  is rejected: update the configuration first.

Read `GITHUB_REPOSITORY`, `INPUT_VERSION` and optional
`CACHED_TARGET_SHA` from the environment and query the GitHub API via
the `gh` CLI (authenticated by `GH_TOKEN`). Exit zero when the release
may proceed.
"""

import base64
import binascii
import json
import os
import sys

import yaml
from publish_mainnet_release import (
    TAG_PREFIX,
    gh_api,
    load_series_config,
    newest_tests_tag,
    parse_version,
    series_transition,
)

SERIES_CONFIG_REPO_PATH = ".github/configs/mainnet_fixture_version.yaml"


def fail(message: str) -> None:
    """Print an error to stderr and exit non-zero."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def cached_target_series(repository: str, target_sha: str) -> tuple[int, int]:
    """Return the release series committed in a cached nightly target."""
    raw = gh_api(
        f"repos/{repository}/contents/{SERIES_CONFIG_REPO_PATH}?ref={target_sha}",
        ok_404=True,
    )
    if not raw:
        fail(
            "the cached nightly predates mainnet_fixture_version.yaml; "
            "dispatch a fresh fill or select a newer nightly"
        )
    try:
        payload = json.loads(raw)
        text = base64.b64decode(payload["content"]).decode()
        config = yaml.safe_load(text)
        fork = config["fork"]
        revision = config["consensus_revision"]
        if (
            not isinstance(fork, int)
            or isinstance(fork, bool)
            or not isinstance(revision, int)
            or isinstance(revision, bool)
            or fork < 0
            or revision < 0
        ):
            raise ValueError("series values must be non-negative integers")
        return fork, revision
    except (
        binascii.Error,
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as e:
        fail(f"the cached nightly has invalid release-series config: {e}")


def main() -> None:
    """Validate the requested version and exit accordingly."""
    repository = os.environ["GITHUB_REPOSITORY"]
    requested_input = os.environ["INPUT_VERSION"]
    requested = parse_version(requested_input)
    if requested is None:
        fail(f"version '{requested_input}' must match vX.Y.Z")
        return

    configured = load_series_config()
    prev_tag = newest_tests_tag(repository)
    if not prev_tag:
        print("No published release yet, any first release is allowed.")
        return
    published = parse_version(prev_tag.removeprefix(TAG_PREFIX))
    assert published is not None

    if requested[:2] == published[:2]:
        if requested <= published:
            fail(
                f"version '{requested_input}' must be greater than the "
                f"newest release ({prev_tag})"
            )
        print(f"{requested_input} continues the published series.")
        return

    state = series_transition(configured, published[:2])
    if state == "current":
        fail(
            f"version '{requested_input}' starts a new series but the "
            f"configuration still selects {configured[0]}."
            f"{configured[1]}: update mainnet_fixture_version.yaml first"
        )
    expected = f"v{configured[0]}.{configured[1]}.0"
    if requested != (configured[0], configured[1], 0):
        fail(
            f"the configured series requires exactly '{expected}', not "
            f"'{requested_input}'"
        )
    cached_target_sha = os.environ.get("CACHED_TARGET_SHA")
    if cached_target_sha:
        target_series = cached_target_series(repository, cached_target_sha)
        if target_series != configured:
            fail(
                f"the cached nightly selects series {target_series[0]}."
                f"{target_series[1]}, not the required {configured[0]}."
                f"{configured[1]}; dispatch a fresh fill or select a "
                "nightly built after the series change"
            )
    print(f"{requested_input} starts the configured series.")


if __name__ == "__main__":
    main()
