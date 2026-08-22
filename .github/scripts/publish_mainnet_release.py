#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Gate and prepare the scheduled mainnet patch release.

Usage: `publish_mainnet_release.py` (all inputs come from the
environment).

Maintainers explicitly select the mainnet `X.Y` release series in
`.github/configs/mainnet_fixture_version.yaml`. Major and
consensus-minor releases are manual. When the latest published release
already matches that series, the first eligible nightly at least 14
days after it automatically publishes accumulated, validated
fixture-content changes as the next `Z` patch.

This script is that gate, run by the `publish` job at the end of the
scheduled nightly fill in `release_fixtures.yaml`. It compares the
newest published `tests@vX.Y.Z` against the configured series:

- Configured series equals the published `X.Y`: publish `vX.Y.Z+1`
  when at least 14 days have elapsed, the merged index root changed and
  the content validates.
  Additions, modifications, removals, renames, filler changes,
  refactors and serialization changes are all ordinary patch content.
- Configured series is `X.Y+1` or `X+1.0`: publish nothing and report
  that the manual `vX.Y.0` release of the configured series is
  required. Its publication starts a new 14-day patch window.
- Any other relation between the configured and the published series
  is a configuration error and fails.

The configuration records semantic release intent, the fixture index
records artifact content. Consensus semantics are never inferred from
fixture differences or changed paths.

Nothing is published either when

- no `tests@vX.Y.Z` tag exists to bump (first releases are manual),
- a `tests@` draft above the newest published version is awaiting
  publish (a manual release in preparation),
- the index root equals the newest release's recorded root (identical
  content, nothing to ship), or
- the content difference cannot be validated: the previous index is
  missing, corrupt or ambiguous, an index holds duplicate fixture
  identities, tests disappeared en masse (a partial fill), the fork
  set changed without a configured fork transition, or the commit
  listing for the notes was capped by the API.

Fixture identity is the (json_path, id) pair. The previous index is
read from the newest release's `fixtures_index.json.gz` asset, falling
back to streaming the early metadata members of its `fixtures.tar.gz`,
so releases predating these assets validate fine.

The `A-tests` label never gates, it only selects which PRs the notes
list. PRs without the label are left out.

Read `GITHUB_REPOSITORY`, `ROOT_HASH` (the merged index root of this
run's fill), `TARGET_SHA` (the commit it built) and `INDEX_DIR` (the
directory holding this run's `fixtures_index.json.gz`) from the
environment and query the GitHub API via the `gh` CLI (authenticated
by `GH_TOKEN`). `MAINNET_VERSION_CONFIG` overrides the series
configuration path (used by the tests). Print `dispatch=true|false`
and `version` as `key=value` lines for `$GITHUB_OUTPUT`, write
`release_notes.md` to the working directory when dispatching and
append the decision to the `$GITHUB_STEP_SUMMARY` file.
"""

import gzip
import json
import os
import re
import subprocess
import sys
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

TAG_PREFIX = "tests@"
TESTS_LABEL = "A-tests"

# Every release the workflow creates carries the merged index root and
# the gzipped index itself as assets, read back by the next gate run.
ROOT_ASSET = "index_root.txt"
INDEX_ASSET = "fixtures_index.json.gz"
TARBALL_ASSET = "fixtures.tar.gz"
# The index sits among the leading `.meta` members of the release
# tarball (paths are sorted and `.meta` sorts before every fixture
# directory), so streaming the front of the tarball recovers it. Other
# metadata files (e.g. `fixtures.ini`) may precede it.
INDEX_TAR_MEMBER = "fixtures/.meta/index.json"
INDEX_TAR_PREFIX = "fixtures/.meta/"
INDEX_SCAN_LIMIT = 16
PATCH_INTERVAL = timedelta(days=14)

SERIES_CONFIG = Path(
    os.environ.get("MAINNET_VERSION_CONFIG")
    or Path(__file__).parents[1] / "configs" / "mainnet_fixture_version.yaml"
)
NOTES_TEMPLATE = (
    Path(__file__).parents[1] / "configs" / "mainnet_release_notes.md"
)
NOTES_FILE = "release_notes.md"

VERSION_RE = re.compile(r"^v([0-9]+)\.([0-9]+)\.([0-9]+)$")
# The squash-merge subject ends in the PR reference, e.g. "(#3123)".
PR_RE = re.compile(r"\(#([0-9]+)\)")


def gh_api(
    path: str,
    paginate: bool = False,
    accept: str | None = None,
    ok_404: bool = False,
) -> str:
    """
    Return the stdout of `gh api <path>`, exiting non-zero on error.

    With *paginate*, follow the Link header through every page and
    return a JSON array of per-page responses (`--slurp`). With
    *accept*, request that media type (e.g. an asset's raw content).
    With *ok_404*, a missing resource returns "" instead of exiting.
    """
    flags = ["--paginate", "--slurp"] if paginate else []
    if accept:
        flags += ["-H", f"Accept: {accept}"]
    result = subprocess.run(
        ["gh", "api", *flags, path], capture_output=True, text=True
    )
    if result.returncode != 0:
        if ok_404 and "HTTP 404" in result.stderr:
            return ""
        print(f"Error: gh api {path} failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


def gh_api_bytes(path: str) -> bytes:
    """Return the raw content behind *path* (a release asset)."""
    result = subprocess.run(
        ["gh", "api", "-H", "Accept: application/octet-stream", path],
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"Error: gh api {path} failed:", file=sys.stderr)
        print(result.stderr.decode(errors="replace"), file=sys.stderr)
        sys.exit(1)
    return result.stdout


def append_summary(text: str) -> None:
    """Append *text* to the GitHub step summary, or stderr if unset."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write(text + "\n")
    else:
        print(text, file=sys.stderr)


def parse_version(version: str) -> tuple[int, int, int] | None:
    """Return the (major, minor, patch) of a `vX.Y.Z` string, or None."""
    m = VERSION_RE.match(version)
    if not m:
        return None
    major, minor, patch = (int(g) for g in m.groups())
    return major, minor, patch


def load_series_config() -> tuple[int, int]:
    """
    Return the maintainer-selected (fork, consensus_revision) series.

    The configuration records semantic release intent. A missing or
    malformed file fails: the automation must never guess the intended
    series.
    """
    try:
        config = yaml.safe_load(SERIES_CONFIG.read_text())
        fork = config["fork"]
        revision = config["consensus_revision"]
        if (
            not isinstance(fork, int)
            or isinstance(fork, bool)
            or not isinstance(revision, int)
            or isinstance(revision, bool)
        ):
            raise TypeError("series values must be integers")
        if fork < 0 or revision < 0:
            raise ValueError("series values must not be negative")
        return fork, revision
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as e:
        print(f"Error: invalid {SERIES_CONFIG.name}: {e}", file=sys.stderr)
        sys.exit(1)


def next_patch_time(release: dict) -> datetime | None:
    """Return the earliest automatic patch time, or None when unknown."""
    published_at = release.get("published_at")
    if not published_at:
        return None
    try:
        published = datetime.fromisoformat(
            str(published_at).replace("Z", "+00:00")
        )
        if published.tzinfo is None:
            raise ValueError("timestamp has no timezone")
    except ValueError as e:
        print(
            f"Error: newest release has invalid published_at: {e}",
            file=sys.stderr,
        )
        sys.exit(1)
    return published + PATCH_INTERVAL


def current_time() -> datetime:
    """Return now in UTC; RELEASE_NOW makes interval tests deterministic."""
    override = os.environ.get("RELEASE_NOW")
    if not override:
        return datetime.now(timezone.utc)
    try:
        value = datetime.fromisoformat(override.replace("Z", "+00:00"))
        if value.tzinfo is None:
            raise ValueError("timestamp has no timezone")
        return value
    except ValueError as e:
        print(f"Error: invalid RELEASE_NOW: {e}", file=sys.stderr)
        sys.exit(1)


def series_transition(
    configured: tuple[int, int], published: tuple[int, int]
) -> str:
    """
    Return the state of the configured series against the published one.

    "current" allows patch automation, "consensus" and "fork" await the
    manual `vX.Y.0` release of the configured series. Every other
    relation is a configuration error and fails safely: the automation
    must never guess an intended series.
    """
    x, y = published
    if configured == (x, y):
        return "current"
    if configured == (x, y + 1):
        return "consensus"
    if configured == (x + 1, 0):
        return "fork"
    fork, revision = configured
    if configured < (x, y):
        reason = "is behind the published series"
    elif fork == x:
        reason = "skips consensus revisions"
    elif fork == x + 1:
        reason = "advances the fork without resetting consensus_revision"
    else:
        reason = "is an invalid fork transition"
    print(
        f"Error: the configured series {fork}.{revision} {reason} "
        f"(published: {x}.{y})",
        file=sys.stderr,
    )
    sys.exit(1)


def newest_tests_tag(repository: str) -> str:
    """
    Return the newest published `tests@vX.Y.Z` tag, or "" when none.

    Draft releases do not create git tags, so the tag listing holds
    exactly the published releases. The listing is paginated in
    ref-name order, not version order, so every page must be fetched
    before taking the maximum. Duplicated in resolve_cached_release.py
    (each script runs standalone), keep the two in sync.
    """
    pages = json.loads(
        gh_api(
            f"repos/{repository}/git/matching-refs/tags/{TAG_PREFIX}",
            paginate=True,
        )
    )
    refs = [ref for page in pages for ref in page]
    tags = [ref["ref"].removeprefix("refs/tags/") for ref in refs]
    versioned = [
        (version, tag)
        for tag in tags
        if (version := parse_version(tag.removeprefix(TAG_PREFIX)))
    ]
    if not versioned:
        return ""
    return max(versioned)[1]


def published_release(repository: str, tag: str) -> dict:
    """
    Return the published release tagged *tag*, or {} when deleted.

    Drafts hold no tag, so the endpoint resolves published releases
    only. A tag whose release object was deleted resolves to {}: its
    fingerprints are unrecoverable, so nothing can be validated against
    it and the automation skips.
    """
    raw = gh_api(f"repos/{repository}/releases/tags/{tag}", ok_404=True)
    return json.loads(raw) if raw else {}


def pending_draft(repository: str, newest: tuple[int, int, int]) -> str | None:
    """
    Return the tag of a `tests@` draft newer than *newest*, or None.

    A pending draft above the newest published version is a manual
    release in preparation, so the automation pauses. Older drafts
    (such as throwaway versions from cached-release test dispatches)
    do not count. The listing is paginated so a draft cannot hide
    behind a long release history.
    """
    pages = json.loads(
        gh_api(f"repos/{repository}/releases?per_page=100", paginate=True)
    )
    releases = [release for page in pages for release in page]
    for release in releases:
        tag = str(release["tag_name"])
        if not release["draft"] or not tag.startswith(TAG_PREFIX):
            continue
        version = parse_version(tag.removeprefix(TAG_PREFIX))
        if version and version > newest:
            return tag
    return None


def release_asset_id(release: dict, name: str) -> int | None:
    """Return the id of the asset called *name*, or None when absent."""
    for asset in release.get("assets") or []:
        if asset["name"] == name:
            return int(asset["id"])
    return None


def release_root(repository: str, release: dict) -> str | None:
    """
    Return the index root recorded on *release*, or None when absent.

    Releases predating the root recording carry no `index_root.txt`
    asset and compare as unknown.
    """
    asset_id = release_asset_id(release, ROOT_ASSET)
    if asset_id is None:
        return None
    content = gh_api(
        f"repos/{repository}/releases/assets/{asset_id}",
        accept="application/octet-stream",
    )
    return content.strip() or None


def index_from_tarball(repository: str, asset_id: int) -> dict | None:
    """
    Return the fixture index inside a release tarball, or None.

    Stream the tarball asset and scan its leading metadata members for
    the index (other `.meta` files such as `fixtures.ini` may precede
    it). Stop without downloading the archive as soon as a fixture
    member appears or the scan limit is hit.
    """
    process = subprocess.Popen(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/octet-stream",
            f"repos/{repository}/releases/assets/{asset_id}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert process.stdout is not None
        with tarfile.open(fileobj=process.stdout, mode="r|gz") as tar:
            for scanned, member in enumerate(tar):
                if member.name == INDEX_TAR_MEMBER:
                    extracted = tar.extractfile(member)
                    if extracted is None:
                        return None
                    return json.load(extracted)
                if (
                    scanned + 1 >= INDEX_SCAN_LIMIT
                    or not member.name.startswith(INDEX_TAR_PREFIX)
                ):
                    return None
        return None
    except (tarfile.TarError, json.JSONDecodeError, OSError):
        return None
    finally:
        process.kill()
        process.wait()


def previous_index(repository: str, release: dict) -> dict | None:
    """
    Return the fixture index recorded on *release*, or None.

    Prefer the dedicated index asset, falling back to the tarball on a
    corrupt one. Releases predating the asset still carry the index
    inside their tarball, so every release since the scheme began can
    be validated against.
    """
    asset_id = release_asset_id(release, INDEX_ASSET)
    if asset_id is not None:
        raw = gh_api_bytes(f"repos/{repository}/releases/assets/{asset_id}")
        try:
            return json.loads(gzip.decompress(raw))
        except (gzip.BadGzipFile, json.JSONDecodeError, EOFError):
            pass
    asset_id = release_asset_id(release, TARBALL_ASSET)
    if asset_id is None:
        return None
    return index_from_tarball(repository, asset_id)


def index_cases(index: dict) -> dict[tuple[str, str], str] | None:
    """
    Return the fixture identity to hash mapping of an index, or None.

    Fixture identity is the (json_path, id) pair. A duplicate identity
    makes the index ambiguous, so None is returned instead of silently
    overwriting an entry.
    """
    cases: dict[tuple[str, str], str] = {}
    for case in index["test_cases"]:
        identity = (case["json_path"], case["id"])
        if identity in cases:
            return None
        cases[identity] = case["fixture_hash"]
    return cases


def merged_test_prs(
    repository: str, prev_tag: str, target_sha: str
) -> tuple[list[str], bool]:
    """
    Return the merged `A-tests` PR subjects in the range and whether
    the listing was complete.

    Walk the commits between *prev_tag* and *target_sha* (the exact
    content difference of the release), take each squash subject's PR
    reference, and keep the PRs that carry the tests label. The compare
    listing is paginated but the API caps very long ranges: a capped
    listing is reported so nothing ships with silently incomplete
    notes. A reference that is not a PR of this repo (a hand-written
    subject) is skipped.
    """
    pages = json.loads(
        gh_api(
            f"repos/{repository}/compare/{prev_tag}...{target_sha}",
            paginate=True,
        )
    )
    commits = [commit for page in pages for commit in page["commits"]]
    total = pages[0]["total_commits"] if pages else 0
    complete = len(commits) == total

    subjects: dict[int, str] = {}
    for commit in commits:
        subject = (commit["commit"]["message"].splitlines() or [""])[0]
        numbers = PR_RE.findall(subject)
        if numbers:
            subjects.setdefault(int(numbers[-1]), subject)

    matching = []
    for number, subject in subjects.items():
        raw = gh_api(f"repos/{repository}/pulls/{number}", ok_404=True)
        if not raw:
            continue
        labels = [label["name"] for label in json.loads(raw)["labels"]]
        if TESTS_LABEL in labels:
            matching.append(subject)
    return matching, complete


def render_notes(
    repository: str,
    version: str,
    prev_tag: str,
    test_prs: str,
    diff_counts: str,
    root: str,
) -> None:
    """Render the repo notes template into `release_notes.md`."""
    releases_url = f"https://github.com/{repository}/releases/tag"
    compare_url = (
        f"https://github.com/{repository}/compare/"
        f"{prev_tag}...{TAG_PREFIX}{version}"
    )
    notes = NOTES_TEMPLATE.read_text().format(
        version=version,
        previous_tag=prev_tag,
        previous_tag_url=f"{releases_url}/{prev_tag.replace('@', '%40')}",
        test_prs=test_prs,
        diff_counts=diff_counts,
        root_hash=root,
        compare_url=compare_url,
    )
    Path(NOTES_FILE).write_text(notes)


def skip(reason: str) -> None:
    """Print the no-release decision and its *reason*."""
    print("dispatch=false")
    append_summary(reason)


def main() -> None:
    """Print the release decision and write the notes and summary."""
    repository = os.environ["GITHUB_REPOSITORY"]
    root = os.environ["ROOT_HASH"]
    target_sha = os.environ["TARGET_SHA"]
    index_dir = Path(os.environ["INDEX_DIR"])
    if not root:
        print(
            "Error: ROOT_HASH is empty, no index was merged",
            file=sys.stderr,
        )
        sys.exit(1)

    configured = load_series_config()
    prev_tag = newest_tests_tag(repository)
    if not prev_tag:
        skip(
            f"No published `{TAG_PREFIX}vX.Y.Z` release exists. Cut the "
            "first mainnet release manually."
        )
        return
    x, y, z = parse_version(  # type: ignore[misc]
        prev_tag.removeprefix(TAG_PREFIX)
    )

    # The configured series is authoritative: maintainers select X.Y,
    # the nightly only ever selects Z.
    state = series_transition(configured, (x, y))
    if state != "current":
        kind = "consensus revision" if state == "consensus" else "fork"
        manual = f"v{configured[0]}.{configured[1]}.0"
        skip(
            f"The configured series acknowledges a new {kind}: the "
            f"manual `{TAG_PREFIX}{manual}` release is required (the "
            "`cached` dispatch may reuse a nightly built after the series "
            "change; otherwise dispatch a fresh fill). "
            "Its publication starts a new 14-day automatic-patch "
            "window."
        )
        return
    version = f"v{x}.{y}.{z + 1}"

    draft_tag = pending_draft(repository, (x, y, z))
    if draft_tag:
        skip(
            f"Draft `{draft_tag}` is awaiting publish. Leaving the "
            "release to its author."
        )
        return

    release = published_release(repository, prev_tag)
    prev_root = release_root(repository, release)
    if prev_root == root:
        skip(
            f"The index root is unchanged since `{prev_tag}`. "
            "Nothing to release."
        )
        return

    due = next_patch_time(release)
    if due is not None and current_time() < due:
        skip(
            "Automatic patches are published at most once every 14 days. "
            f"The next patch window opens at `{due.isoformat()}`; changes "
            "remain in the nightly artifact until then."
        )
        return

    current_index = json.loads(
        gzip.decompress((index_dir / INDEX_ASSET).read_bytes())
    )
    current_cases = index_cases(current_index)
    if current_cases is None:
        print(
            "Error: this run's index holds duplicate fixture identities",
            file=sys.stderr,
        )
        sys.exit(1)

    prev_index = previous_index(repository, release)
    if prev_index is not None and prev_index.get("root_hash") == root:
        # A release without the root asset still records its root
        # inside the index, so the equality gate works there too.
        skip(
            f"The index root is unchanged since `{prev_tag}`. "
            "Nothing to release."
        )
        return
    if prev_index is None:
        skip(
            f"The index of `{prev_tag}` could not be recovered, so the "
            "content difference cannot be validated. Cut a manual "
            "release to restore the baseline."
        )
        return
    prev_cases = index_cases(prev_index)
    if prev_cases is None:
        skip(
            f"The index of `{prev_tag}` holds duplicate fixture "
            "identities, so the content difference cannot be validated. "
            "Cut a manual release to restore the baseline."
        )
        return

    # Validate the content difference. The counts never select the
    # version, they only guard against shipping a broken artifact and
    # inform the notes.
    added = [t for t in current_cases if t not in prev_cases]
    removed = [t for t in prev_cases if t not in current_cases]
    changed = [
        t
        for t, fixture_hash in current_cases.items()
        if t in prev_cases and prev_cases[t] != fixture_hash
    ]
    counts = (
        f"{len(added)} added, {len(removed)} removed, {len(changed)} changed"
    )
    # Deliberate removals are far smaller than a fork range: a mass
    # disappearance means a partial fill or a collection regression.
    if len(removed) > max(1000, len(prev_cases) // 20):
        skip(
            f"{len(removed)} tests vanished since `{prev_tag}`, which "
            "looks like a partial fill rather than a deliberate "
            "removal. Not releasing."
        )
        return
    prev_forks = set(prev_index.get("forks") or [])
    current_forks = set(current_index.get("forks") or [])
    if prev_forks and prev_forks != current_forks:
        skip(
            "The fork set of the fixture index changed "
            f"({sorted(prev_forks ^ current_forks)}) within the "
            "configured series. A new mainnet fork needs the configured "
            "fork bumped, any other fill-range change needs a manual "
            "release to accept the new fork set."
        )
        return

    pr_subjects, complete = merged_test_prs(repository, prev_tag, target_sha)
    if not complete:
        skip(
            f"The commit listing for `{prev_tag}...{target_sha}` was "
            "capped by the API, so the notes cannot be completed. Cut "
            "a manual release."
        )
        return
    test_prs = (
        "\n".join(f"- {subject}" for subject in pr_subjects)
        if pr_subjects
        else "None."
    )

    render_notes(repository, version, prev_tag, test_prs, counts, root)

    print("dispatch=true")
    print(f"version={version}")
    detail = (
        "Merged `A-tests` PRs:\n"
        + "\n".join(f"- {subject}" for subject in pr_subjects)
        if pr_subjects
        else "No merged `A-tests` PRs in the range."
    )
    append_summary(
        f"Publishing `{TAG_PREFIX}{version}` (supersedes `{prev_tag}`). "
        f"{counts} tests.\n{detail}"
    )


if __name__ == "__main__":
    main()
