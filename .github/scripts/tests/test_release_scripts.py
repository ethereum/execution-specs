"""
Test the CI release helper scripts.

Each test invokes the script via `uv run` to validate the actual CLI
interface, matching how GitHub Actions calls them.
"""

import base64
import gzip
import io
import json
import os
import subprocess
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent
REPO_ROOT = SCRIPTS_DIR.parent.parent

BUILD_MATRIX_SCRIPT = SCRIPTS_DIR / "generate_build_matrix.py"
TARBALL_SCRIPT = SCRIPTS_DIR / "create_release_tarball.py"
MERGE_INDEX_SCRIPT = SCRIPTS_DIR / "merge_index_files.py"
CHECK_COMMITS_SCRIPT = SCRIPTS_DIR / "check_new_commits.py"
RESOLVE_CACHED_SCRIPT = SCRIPTS_DIR / "resolve_cached_release.py"
PUBLISH_MAINNET_SCRIPT = SCRIPTS_DIR / "publish_mainnet_release.py"
VALIDATE_MAINNET_SCRIPT = SCRIPTS_DIR / "validate_mainnet_release.py"


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess:
    """Run a uv inline-deps script and return the result."""
    return subprocess.run(
        ["uv", "run", "-q", str(script), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def parse_matrix_output(stdout: str) -> dict[str, str]:
    """Parse key=value output from generate_build_matrix.py."""
    return {
        k: v
        for line in stdout.strip().splitlines()
        if "=" in line
        for k, v in [line.split("=", 1)]
    }


class TestGenerateBuildMatrix:
    """Test generate_build_matrix.py."""

    def test_split_feature_produces_entries_per_range(self):
        """Verify a split feature expands into one entry per range."""
        result = run_script(BUILD_MATRIX_SCRIPT, "tests", "v24.0.0")
        assert result.returncode == 0
        out = parse_matrix_output(result.stdout)
        matrix = json.loads(out["build_matrix"])
        assert len(matrix) > 1
        assert out["feature_name"] == "tests"
        assert out["combine_labels"] != ""
        labels = [e["label"] for e in matrix]
        assert all(lbl != "" for lbl in labels)
        assert all(e["from_fork"] != "" for e in matrix)
        assert all(e["until_fork"] != "" for e in matrix)

    def test_unsplit_feature_produces_single_entry(self):
        """Verify a feature without fork-ranges produces one entry."""
        result = run_script(BUILD_MATRIX_SCRIPT, "benchmark", "v24.0.0")
        assert result.returncode == 0
        out = parse_matrix_output(result.stdout)
        matrix = json.loads(out["build_matrix"])
        assert len(matrix) == 1
        assert out["feature_name"] == "benchmark"
        assert out["combine_labels"] == ""
        assert matrix[0]["label"] == ""
        assert matrix[0]["from_fork"] == ""
        assert matrix[0]["until_fork"] == ""

    def test_devnet_name_resolves_to_shared_feature(self):
        """Verify a <feat>-devnet name resolves to the devnet feature."""
        result = run_script(
            BUILD_MATRIX_SCRIPT, "bal-devnet", "v7.0.0", "devnets/bal/7"
        )
        assert result.returncode == 0
        out = parse_matrix_output(result.stdout)
        matrix = json.loads(out["build_matrix"])
        assert out["feature_name"] == "bal-devnet"
        # Entries keep the friendly name, not the shared "devnet" key.
        assert all(e["feature"] == "bal-devnet" for e in matrix)

    def test_unknown_feature_fails(self):
        """Verify error exit for unknown feature name."""
        result = run_script(BUILD_MATRIX_SCRIPT, "nonexistent", "v1.0.0")
        assert result.returncode == 1
        assert "not found" in result.stderr

    def test_no_args_fails(self):
        """Verify error exit when no arguments provided."""
        result = run_script(BUILD_MATRIX_SCRIPT)
        assert result.returncode == 1
        assert "Usage" in result.stderr

    def test_output_is_valid_github_actions_format(self):
        """Verify output lines are key=value for GITHUB_OUTPUT."""
        result = run_script(BUILD_MATRIX_SCRIPT, "tests", "v24.0.0")
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 3
        assert lines[0].startswith("build_matrix=")
        assert lines[1].startswith("feature_name=")
        assert lines[2].startswith("combine_labels=")


class TestValidateInputs:
    """Test the release input validation in generate_build_matrix.py."""

    def test_bad_version_fails(self):
        """Verify a non vX.Y.Z version is rejected."""
        result = run_script(BUILD_MATRIX_SCRIPT, "tests", "24.0.0")
        assert result.returncode == 1
        assert "must match vX.Y.Z" in result.stderr

    def test_empty_feature_fails(self):
        """Verify an empty feature name is rejected."""
        result = run_script(BUILD_MATRIX_SCRIPT, "", "v1.0.0")
        assert result.returncode == 1
        assert "feature name is empty" in result.stderr

    def test_bare_devnet_fails(self):
        """Verify a bare `devnet` feature name is rejected."""
        result = run_script(
            BUILD_MATRIX_SCRIPT, "devnet", "v7.0.0", "devnets/bal/7"
        )
        assert result.returncode == 1
        assert "require a <feat>- prefix" in result.stderr

    def test_devnet_index_in_feature_name_fails(self):
        """Verify `<feat>-devnet-<n>` is rejected with a suggestion."""
        result = run_script(
            BUILD_MATRIX_SCRIPT, "bal-devnet-7", "v7.0.0", "devnets/bal/7"
        )
        assert result.returncode == 1
        assert "did you mean feature=bal-devnet version=v7.0.0" in (
            result.stderr
        )

    def test_devnet_without_branch_fails(self):
        """Verify a `<feat>-devnet` release requires a branch."""
        result = run_script(BUILD_MATRIX_SCRIPT, "bal-devnet", "v7.0.0")
        assert result.returncode == 1
        assert "require a 'branch' input" in result.stderr

    def test_devnet_branch_wrong_shape_fails(self):
        """Verify a branch outside `devnets/<feat>/<n>` is rejected."""
        result = run_script(
            BUILD_MATRIX_SCRIPT, "bal-devnet", "v7.0.0", "bal-devnet-7"
        )
        assert result.returncode == 1
        assert "could not parse a devnet number" in result.stderr

    def test_devnet_major_must_match_branch_number(self):
        """Verify the major version must equal the branch devnet number."""
        result = run_script(
            BUILD_MATRIX_SCRIPT, "bal-devnet", "v3.0.0", "devnets/bal/7"
        )
        assert result.returncode == 1
        assert "must equal the devnet number" in result.stderr

    def test_devnet_matching_major_passes(self):
        """Verify a major equal to the branch devnet number passes."""
        result = run_script(
            BUILD_MATRIX_SCRIPT,
            "glamsterdam-devnet",
            "v6.0.0",
            "devnets/glamsterdam/6",
        )
        assert result.returncode == 0
        out = parse_matrix_output(result.stdout)
        assert out["feature_name"] == "glamsterdam-devnet"

    def test_unknown_evm_fails(self):
        """Verify an evm override missing from evm.yaml is rejected."""
        result = run_script(
            BUILD_MATRIX_SCRIPT, "tests", "v24.0.0", "", "nonexistent"
        )
        assert result.returncode == 1
        assert "not a key" in result.stderr

    def test_known_evm_passes(self):
        """Verify an evm override that is a key in evm.yaml passes."""
        result = run_script(
            BUILD_MATRIX_SCRIPT, "tests", "v24.0.0", "", "evmone"
        )
        assert result.returncode == 0


# Fake `gh` served from PATH: answers the API calls the commit-check,
# cached-release and draft-gate scripts make with canned JSON from env
# vars, and fails loudly on any other (or unconfigured) call. The API path is
# the last argument (flags such as `--paginate --slurp` may precede
# it). Per-run artifact responses come from
# `FAKE_GH_ARTIFACTS_<run_id>`, falling back to `FAKE_GH_ARTIFACTS`.
FAKE_GH = """#!/usr/bin/env bash
path="${@: -1}"
case "$path" in
  *actions/workflows*) response="$FAKE_GH_RUNS" ;;
  */artifacts)
    run_id="${path##*/runs/}"
    run_id="${run_id%%/*}"
    var="FAKE_GH_ARTIFACTS_${run_id}"
    response="${!var:-$FAKE_GH_ARTIFACTS}"
    ;;
  *matching-refs*) response="$FAKE_GH_TAGS" ;;
  *contents/.github/configs/mainnet_fixture_version.yaml*)
    response="$FAKE_GH_SERIES_CONFIG"
    ;;
  *releases/assets/*)
    asset="${path##*/assets/}"
    file_var="FAKE_GH_ASSET_FILE_${asset}"
    if [ -n "${!file_var:-}" ]; then
      cat "${!file_var}"
      exit 0
    fi
    var="FAKE_GH_ASSET_${asset}"
    response="${!var}"
    ;;
  *releases/tags/*) response="$FAKE_GH_RELEASE_TAG" ;;
  *"releases?"*) response="$FAKE_GH_RELEASES" ;;
  *pulls/*)
    pr="${path##*/pulls/}"
    var="FAKE_GH_PR_${pr}"
    response="${!var:-$FAKE_GH_PR}"
    ;;
  *compare/tests@*) response="$FAKE_GH_COMPARE_TAG" ;;
  *compare*) response="$FAKE_GH_COMPARE" ;;
  *) response="" ;;
esac
if [ "$response" = "__404__" ]; then
  echo "gh: Not Found (HTTP 404)" >&2
  exit 1
fi
if [ -z "$response" ]; then
  echo "unexpected gh call: $*" >&2
  exit 1
fi
printf '%s' "$response"
"""

# Canned artifact-list responses for the fake `gh`.
LIVE_ARTIFACTS = '{"artifacts": [{"expired": false}]}'
EXPIRED_ARTIFACTS = '{"artifacts": [{"expired": true}]}'
NO_ARTIFACTS = '{"artifacts": []}'


class TestCheckNewCommits:
    """Test check_new_commits.py."""

    def run_check(
        self,
        tmp_path: Path,
        event_name: str,
        runs: str = "",
        compare: str = "",
        artifacts: str = "",
        per_run_artifacts: dict[int, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess, Path]:
        """Run the script with a fake `gh` on PATH; return it + summary."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(FAKE_GH)
        fake_gh.chmod(0o755)

        summary = tmp_path / "summary.md"
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        env["GITHUB_EVENT_NAME"] = event_name
        env["GITHUB_REPOSITORY"] = "ethereum/execution-specs"
        env["GITHUB_SHA"] = "b" * 40
        env["GITHUB_STEP_SUMMARY"] = str(summary)
        env["FAKE_GH_RUNS"] = runs
        env["FAKE_GH_COMPARE"] = compare
        env["FAKE_GH_ARTIFACTS"] = artifacts
        for run_id, response in (per_run_artifacts or {}).items():
            env[f"FAKE_GH_ARTIFACTS_{run_id}"] = response

        result = subprocess.run(
            ["uv", "run", "-q", str(CHECK_COMMITS_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )
        return result, summary

    def test_dispatch_always_runs_without_api_calls(self, tmp_path):
        """Verify a manual dispatch runs and never calls the API."""
        # The fake `gh` fails every call (no canned responses), so a
        # zero exit proves the script made no API call.
        result, summary = self.run_check(tmp_path, "workflow_dispatch")
        assert result.returncode == 0
        assert result.stdout.strip() == "run=true"
        assert not summary.exists()

    def test_schedule_without_prior_run_fills_baseline(self, tmp_path):
        """Verify the first scheduled run fills to get a baseline."""
        result, summary = self.run_check(
            tmp_path, "schedule", runs='{"workflow_runs": []}'
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "run=true"
        assert "no previous successful" in summary.read_text()

    @staticmethod
    def run_json(
        age: timedelta, head_sha: str = "b" * 40, run_id: int = 1
    ) -> dict:
        """Return one workflow-run object created *age* ago."""
        created = datetime.now(timezone.utc) - age
        return {
            "id": run_id,
            "head_sha": head_sha,
            "created_at": created.isoformat(),
        }

    @classmethod
    def runs_json(
        cls, age: timedelta, head_sha: str = "b" * 40, run_id: int = 1
    ) -> str:
        """Return a last-successful-run response created *age* ago."""
        return json.dumps(
            {"workflow_runs": [cls.run_json(age, head_sha, run_id)]}
        )

    def test_schedule_with_new_commits_runs(self, tmp_path):
        """Verify new commits since the baseline trigger a run."""
        commit = {
            "sha": "abcdef1" + "0" * 33,
            "commit": {"message": "feat(x): subject\n\nbody"},
        }
        result, summary = self.run_check(
            tmp_path,
            "schedule",
            runs=self.runs_json(timedelta(hours=25), head_sha="a" * 40),
            compare=json.dumps({"commits": [commit]}),
            artifacts=LIVE_ARTIFACTS,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "run=true"
        text = summary.read_text()
        assert "### Commits since last successful nightly fill" in text
        # Short SHA plus the commit subject, without the body.
        assert "- abcdef1 feat(x): subject" in text
        assert "body" not in text

    def test_schedule_without_new_commits_skips(self, tmp_path):
        """Verify no commits since a recent baseline skips the run."""
        result, summary = self.run_check(
            tmp_path,
            "schedule",
            # Just inside the refresh age: pin the four-day boundary.
            runs=self.runs_json(timedelta(days=3, hours=23)),
            compare=json.dumps({"commits": []}),
            artifacts=LIVE_ARTIFACTS,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "run=false"
        assert "skipping" in summary.read_text()

    def test_schedule_stale_quiet_baseline_refreshes(self, tmp_path):
        """Verify a quiet nightly re-runs once its artifact nears expiry."""
        result, summary = self.run_check(
            tmp_path,
            "schedule",
            runs=self.runs_json(timedelta(days=4, hours=1)),
            compare=json.dumps({"commits": []}),
            artifacts=LIVE_ARTIFACTS,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "run=true"
        assert "refreshing" in summary.read_text()

    def test_schedule_skip_runs_do_not_reset_refresh(self, tmp_path):
        """
        Verify skip-runs neither advance the baseline nor its clock.

        A quiet nightly that skips its build still concludes as a
        successful scheduled run; if it counted as the baseline, a
        stretch of skip-runs would keep resetting the refresh clock
        while the last real artifact quietly expired.
        """
        runs = json.dumps(
            {
                "workflow_runs": [
                    # Newest success skipped its build: no artifacts.
                    self.run_json(timedelta(hours=1), run_id=2),
                    # The last real fill is past the refresh age.
                    self.run_json(timedelta(days=4, hours=1), run_id=1),
                ]
            }
        )
        result, summary = self.run_check(
            tmp_path,
            "schedule",
            runs=runs,
            compare=json.dumps({"commits": []}),
            per_run_artifacts={2: NO_ARTIFACTS, 1: LIVE_ARTIFACTS},
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "run=true"
        assert "refreshing" in summary.read_text()

    def test_schedule_dead_artifact_refills(self, tmp_path):
        """Verify a fill whose artifact is gone refills immediately."""
        result, summary = self.run_check(
            tmp_path,
            "schedule",
            runs=self.runs_json(timedelta(days=1)),
            compare=json.dumps({"commits": []}),
            artifacts=EXPIRED_ARTIFACTS,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "run=true"
        assert "no live fixture artifact" in summary.read_text()

    def test_gh_failure_fails_the_check(self, tmp_path):
        """Verify a failing `gh` call fails the script."""
        result, _ = self.run_check(tmp_path, "schedule")
        assert result.returncode == 1
        assert "gh api" in result.stderr


# Canned responses for the cached-release script. Unlike the commit
# check, it matches artifacts by the commit-derived
# `fixtures_<short sha>` name, so the canned listings are built
# per head SHA. The tag listing is fetched with `--paginate --slurp`
# (a JSON array of pages); spreading the refs over two pages makes
# every test exercise the page flattening.
TESTS_TAGS = json.dumps(
    [
        [{"ref": "refs/tags/tests@v3.1.2"}],
        [{"ref": "refs/tags/tests@v4.0.0"}],
    ]
)
NO_TAGS = "[[]]"
UP_TO_DATE = json.dumps({"status": "identical", "commits": []})


def artifact_listing(head_sha: str, expired: bool = False) -> str:
    """Return an artifact listing with a tarball named for *head_sha*."""
    return json.dumps(
        {
            "artifacts": [
                {
                    "name": f"fixtures_{head_sha[:7]}",
                    "expired": expired,
                }
            ]
        }
    )


class TestResolveCachedRelease:
    """Test resolve_cached_release.py."""

    def run_resolve(
        self,
        tmp_path: Path,
        version: str,
        feature: str = "tests",
        branch: str = "",
        commit: str = "",
        runs: str = "",
        artifacts: str = "",
        per_run_artifacts: dict[int, str] | None = None,
        tags: str = "",
        compare: str = "",
        tag_compare: str = UP_TO_DATE,
    ) -> tuple[subprocess.CompletedProcess, Path]:
        """Run the script with a fake `gh` on PATH; return it + summary."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(FAKE_GH)
        fake_gh.chmod(0o755)

        summary = tmp_path / "summary.md"
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        env["GITHUB_REPOSITORY"] = "ethereum/execution-specs"
        env["GITHUB_SHA"] = "b" * 40
        env["GITHUB_STEP_SUMMARY"] = str(summary)
        env["INPUT_VERSION"] = version
        env["INPUT_FEATURE"] = feature
        env["INPUT_BRANCH"] = branch
        env["INPUT_COMMIT"] = commit
        env["FAKE_GH_RUNS"] = runs
        env["FAKE_GH_ARTIFACTS"] = artifacts
        env["FAKE_GH_TAGS"] = tags
        env["FAKE_GH_COMPARE"] = compare
        env["FAKE_GH_COMPARE_TAG"] = tag_compare
        for run_id, response in (per_run_artifacts or {}).items():
            env[f"FAKE_GH_ARTIFACTS_{run_id}"] = response

        result = subprocess.run(
            ["uv", "run", "-q", str(RESOLVE_CACHED_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )
        return result, summary

    @staticmethod
    def parse_outputs(stdout: str) -> dict[str, str]:
        """Parse the key=value lines written for `$GITHUB_OUTPUT`."""
        return dict(line.split("=", 1) for line in stdout.strip().splitlines())

    @staticmethod
    def runs_json(*runs: dict) -> str:
        """Return a workflow-runs listing response."""
        return json.dumps({"workflow_runs": list(runs)})

    def test_reuses_newest_run_with_live_artifact(self, tmp_path):
        """Verify skip-runs and expired fills are passed over."""
        commit = {
            "sha": "abcdef1" + "0" * 33,
            "commit": {"message": "feat(x): subject\n\nbody"},
        }
        result, summary = self.run_resolve(
            tmp_path,
            "v4.0.1",
            runs=self.runs_json(
                # Newest success skipped its build: no artifacts.
                {"id": 3, "head_sha": "c" * 40},
                {"id": 2, "head_sha": "a" * 40},
                {"id": 1, "head_sha": "d" * 40},
            ),
            per_run_artifacts={
                3: NO_ARTIFACTS,
                2: artifact_listing("a" * 40),
                1: artifact_listing("d" * 40, expired=True),
            },
            tags=TESTS_TAGS,
            compare=json.dumps({"status": "ahead", "commits": [commit]}),
        )
        assert result.returncode == 0
        out = self.parse_outputs(result.stdout)
        assert out["run_id"] == "2"
        assert out["target_sha"] == "a" * 40
        assert out["artifact_name"] == "fixtures_aaaaaaa"
        text = summary.read_text()
        assert "### Commits NOT included in this release" in text
        # Short SHA plus the commit subject, without the body.
        assert "- abcdef1 feat(x): subject" in text
        assert "body" not in text

    def test_up_to_date_nightly_resolves_cleanly(self, tmp_path):
        """Verify no missing-commit section when nothing landed since."""
        result, summary = self.run_resolve(
            tmp_path,
            "v4.0.1",
            runs=self.runs_json({"id": 2, "head_sha": "b" * 40}),
            artifacts=artifact_listing("b" * 40),
            tags=TESTS_TAGS,
            compare=UP_TO_DATE,
        )
        assert result.returncode == 0
        text = summary.read_text()
        assert "up to date" in text
        assert "NOT included" not in text

    def test_first_release_without_tags_resolves(self, tmp_path):
        """Verify a cached release works before any tests@ tag exists."""
        result, _ = self.run_resolve(
            tmp_path,
            "v1.0.0",
            runs=self.runs_json({"id": 2, "head_sha": "b" * 40}),
            artifacts=artifact_listing("b" * 40),
            tags=NO_TAGS,
            compare=UP_TO_DATE,
        )
        assert result.returncode == 0
        assert self.parse_outputs(result.stdout)["run_id"] == "2"

    def test_non_tests_feature_fails(self, tmp_path):
        """Verify only the tests feature can release cached."""
        # The fake `gh` fails every call (no canned responses), so a
        # clean feature error proves the guard fires before the API.
        result, _ = self.run_resolve(tmp_path, "v4.0.1", feature="bal-devnet")
        assert result.returncode == 1
        assert "only available for feature=tests" in result.stderr

    def test_branch_input_fails(self, tmp_path):
        """Verify a cached release rejects a branch input."""
        result, _ = self.run_resolve(
            tmp_path, "v4.0.1", branch="devnets/bal/7"
        )
        assert result.returncode == 1
        assert "drop the `branch` input" in result.stderr

    def test_bad_version_format_fails(self, tmp_path):
        """Verify a non vX.Y.Z version is rejected before any API call."""
        result, _ = self.run_resolve(tmp_path, "4.0.1")
        assert result.returncode == 1
        assert "must match vX.Y.Z" in result.stderr

    def test_version_not_greater_than_newest_tag_fails(self, tmp_path):
        """Verify the version must move past the newest tests@ tag."""
        result, _ = self.run_resolve(tmp_path, "v4.0.0", tags=TESTS_TAGS)
        assert result.returncode == 1
        assert "must be greater" in result.stderr
        assert "tests@v4.0.0" in result.stderr

    def test_no_reusable_run_fails(self, tmp_path):
        """Verify a helpful error when every artifact has expired."""
        result, _ = self.run_resolve(
            tmp_path,
            "v4.0.1",
            runs=self.runs_json({"id": 2, "head_sha": "a" * 40}),
            artifacts=artifact_listing("a" * 40, expired=True),
            tags=TESTS_TAGS,
        )
        assert result.returncode == 1
        assert "dispatch a fresh fill instead" in result.stderr

    def test_mismatched_artifact_name_is_skipped(self, tmp_path):
        """Verify an artifact named for another commit is not reused."""
        result, _ = self.run_resolve(
            tmp_path,
            "v4.0.1",
            runs=self.runs_json({"id": 2, "head_sha": "a" * 40}),
            # Live, but named for a different commit than the run built.
            artifacts=artifact_listing("f" * 40),
            tags=TESTS_TAGS,
        )
        assert result.returncode == 1
        assert "dispatch a fresh fill instead" in result.stderr

    def test_commit_input_selects_that_nightly(self, tmp_path):
        """Verify `commit` picks an older nightly over the newest."""
        result, _ = self.run_resolve(
            tmp_path,
            "v4.0.1",
            commit="d" * 7,
            runs=self.runs_json(
                {"id": 3, "head_sha": "c" * 40},
                {"id": 2, "head_sha": "a" * 40},
                {"id": 1, "head_sha": "d" * 40},
            ),
            per_run_artifacts={
                3: NO_ARTIFACTS,
                2: artifact_listing("a" * 40),
                1: artifact_listing("d" * 40),
            },
            tags=TESTS_TAGS,
            compare=UP_TO_DATE,
        )
        assert result.returncode == 0
        out = self.parse_outputs(result.stdout)
        assert out["run_id"] == "1"
        assert out["target_sha"] == "d" * 40
        assert out["artifact_name"] == "fixtures_ddddddd"

    def test_commit_input_without_match_fails(self, tmp_path):
        """Verify a commit with no live nightly lists the candidates."""
        result, _ = self.run_resolve(
            tmp_path,
            "v4.0.1",
            commit="beef111",
            runs=self.runs_json({"id": 2, "head_sha": "a" * 40}),
            artifacts=artifact_listing("a" * 40),
            tags=TESTS_TAGS,
        )
        assert result.returncode == 1
        assert "was built at beef111" in result.stderr
        assert "aaaaaaa" in result.stderr

    def test_bad_commit_format_fails(self, tmp_path):
        """Verify a malformed commit is rejected before any lookup."""
        result, _ = self.run_resolve(
            tmp_path, "v4.0.1", commit="xyz", tags=TESTS_TAGS
        )
        assert result.returncode == 1
        assert "hex characters" in result.stderr

    def test_release_behind_previous_fails(self, tmp_path):
        """Verify a nightly older than the newest release is rejected."""
        result, _ = self.run_resolve(
            tmp_path,
            "v4.0.1",
            runs=self.runs_json({"id": 2, "head_sha": "a" * 40}),
            artifacts=artifact_listing("a" * 40),
            tags=TESTS_TAGS,
            tag_compare=json.dumps({"status": "behind", "commits": []}),
        )
        assert result.returncode == 1
        assert "must not regress content" in result.stderr

    def test_diverged_nightly_fails(self, tmp_path):
        """Verify a nightly off the branch history is not reused."""
        result, _ = self.run_resolve(
            tmp_path,
            "v4.0.1",
            runs=self.runs_json({"id": 2, "head_sha": "a" * 40}),
            artifacts=artifact_listing("a" * 40),
            tags=TESTS_TAGS,
            compare=json.dumps({"status": "diverged", "commits": []}),
        )
        assert result.returncode == 1
        assert "not an ancestor" in result.stderr

    def test_gh_failure_fails_the_resolution(self, tmp_path):
        """Verify a failing `gh` call fails the script."""
        result, _ = self.run_resolve(tmp_path, "v4.0.1")
        assert result.returncode == 1
        assert "gh api" in result.stderr


class TestCreateReleaseTarball:
    """Test create_release_tarball.py."""

    def test_tarball_structure(self, tmp_path):
        """Verify tarball has fixtures/ prefix and correct contents."""
        src = tmp_path / "fixtures"
        (src / "blockchain_tests" / "for_cancun").mkdir(parents=True)
        (src / "blockchain_tests_engine_x" / "pre_alloc").mkdir(parents=True)
        (src / ".meta").mkdir()

        (src / "blockchain_tests" / "for_cancun" / "t.json").write_text("{}")
        pre_alloc = src / "blockchain_tests_engine_x" / "pre_alloc"
        (pre_alloc / "g.json").write_text("{}")
        (src / ".meta" / "fixtures.ini").write_text("[meta]")

        out = tmp_path / "output.tar.gz"
        result = run_script(TARBALL_SCRIPT, str(src), str(out))
        assert result.returncode == 0
        assert out.exists()

        with tarfile.open(out, "r:gz") as tar:
            names = sorted(tar.getnames())

        assert all(n.startswith("fixtures/") for n in names)
        assert "fixtures/blockchain_tests/for_cancun/t.json" in names
        assert "fixtures/blockchain_tests_engine_x/pre_alloc/g.json" in names
        assert "fixtures/.meta/fixtures.ini" in names

    def test_excludes_non_fixture_files(self, tmp_path):
        """Verify .log, .html, etc. are excluded from tarball."""
        src = tmp_path / "fixtures"
        src.mkdir()
        (src / "test.json").write_text("{}")
        (src / "debug.log").write_text("log")
        (src / "report.html").write_text("<html>")
        (src / "data.csv").write_text("a,b")

        out = tmp_path / "output.tar.gz"
        result = run_script(TARBALL_SCRIPT, str(src), str(out))
        assert result.returncode == 0

        with tarfile.open(out, "r:gz") as tar:
            names = tar.getnames()

        assert "fixtures/test.json" in names
        assert len(names) == 1

    def test_nonexistent_dir_fails(self, tmp_path):
        """Verify error for non-existent source directory."""
        result = run_script(
            TARBALL_SCRIPT,
            str(tmp_path / "nope"),
            str(tmp_path / "out.tar.gz"),
        )
        assert result.returncode == 1
        assert "not a directory" in result.stderr

    def test_no_args_fails(self):
        """Verify error when no arguments provided."""
        result = run_script(TARBALL_SCRIPT)
        assert result.returncode == 1
        assert "Usage" in result.stderr


def _run_merge_script(
    *args: str,
) -> subprocess.CompletedProcess:
    """Run merge_index_files.py via uv run python."""
    return subprocess.run(
        ["uv", "run", "python", str(MERGE_INDEX_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


class TestMergeIndexFiles:
    """Test merge_index_files.py."""

    def _write_index(self, fixture_dir: Path, index_data: dict) -> None:
        """Write a .meta/index.json file in the given directory."""
        meta = fixture_dir / ".meta"
        meta.mkdir(parents=True, exist_ok=True)
        (meta / "index.json").write_text(json.dumps(index_data))

    def test_merges_two_index_files(self, tmp_path):
        """Verify merging two fixture dirs produces a combined index."""
        dir_a = tmp_path / "fixtures__cancun"
        dir_b = tmp_path / "fixtures__prague"
        output = tmp_path / "combined" / ".meta" / "index.json"

        self._write_index(
            dir_a,
            {
                "root_hash": None,
                "created_at": "2026-01-01T00:00:00",
                "test_count": 1,
                "forks": ["Cancun"],
                "fixture_formats": ["state_test"],
                "test_cases": [
                    {
                        "id": "test_a",
                        "json_path": "state_tests/for_cancun/t.json",
                        "fixture_hash": "0x" + "11" * 32,
                        "fork": "Cancun",
                        "format": "state_test",
                    }
                ],
            },
        )
        self._write_index(
            dir_b,
            {
                "root_hash": None,
                "created_at": "2026-01-01T00:00:00",
                "test_count": 1,
                "forks": ["Prague"],
                "fixture_formats": ["blockchain_test"],
                "test_cases": [
                    {
                        "id": "test_b",
                        "json_path": "blockchain_tests/for_prague/t.json",
                        "fixture_hash": "0x" + "22" * 32,
                        "fork": "Prague",
                        "format": "blockchain_test",
                    }
                ],
            },
        )

        result = _run_merge_script(
            str(output),
            str(dir_a),
            str(dir_b),
        )
        assert result.returncode == 0
        assert output.exists()

        merged = json.loads(output.read_text())
        assert merged["test_count"] == 2
        assert len(merged["test_cases"]) == 2
        assert merged["root_hash"] is not None

    def test_skips_dirs_without_index(self, tmp_path):
        """Verify directories without .meta/index.json are skipped."""
        dir_a = tmp_path / "fixtures__cancun"
        dir_a.mkdir()
        dir_b = tmp_path / "fixtures__empty"
        dir_b.mkdir()
        output = tmp_path / "out.json"

        self._write_index(
            dir_a,
            {
                "root_hash": None,
                "created_at": "2026-01-01T00:00:00",
                "test_count": 1,
                "forks": ["Cancun"],
                "fixture_formats": ["state_test"],
                "test_cases": [
                    {
                        "id": "test_a",
                        "json_path": "state_tests/t.json",
                        "fixture_hash": "0x" + "11" * 32,
                        "fork": "Cancun",
                        "format": "state_test",
                    }
                ],
            },
        )

        result = _run_merge_script(str(output), str(dir_a), str(dir_b))
        assert result.returncode == 0
        assert output.exists()

        merged = json.loads(output.read_text())
        assert merged["test_count"] == 1

    def test_no_args_fails(self):
        """Verify error when no arguments provided."""
        result = _run_merge_script()
        assert result.returncode == 1
        assert "Usage" in result.stderr


FRESH_ROOT = "0x" + "11" * 32
OLD_ROOT = "0x" + "22" * 32

TEST_A = "tests/berlin/test_foo.py::test_a[fork_Berlin-blockchain_test]"
TEST_B = "tests/osaka/test_bar.py::test_b[fork_Osaka-state_test]"
HASH_A = "0x" + "aa" * 32
HASH_B = "0x" + "bb" * 32
HASH_C = "0x" + "cc" * 32


def release_json(
    release_id: int,
    tag: str,
    draft: bool = True,
    asset_ids: dict[str, int] | None = None,
    published_at: str = "2026-07-01T00:00:00Z",
) -> dict:
    """Return a canned release object with named assets."""
    return {
        "id": release_id,
        "tag_name": tag,
        "draft": draft,
        "published_at": published_at,
        "assets": [
            {"id": asset_id, "name": name}
            for name, asset_id in (asset_ids or {}).items()
        ],
    }


def index_json(
    cases: dict[str, str] | None = None,
    forks: list[str] | None = None,
    root: str = FRESH_ROOT,
    raw_cases: list[dict] | None = None,
) -> dict:
    """
    Return a canned fixture index.

    *cases* maps test ids to fixture hashes with a json_path derived
    from the id; *raw_cases* supplies full test-case entries when the
    (json_path, id) identity itself is under test.
    """
    test_cases = raw_cases or [
        {
            "id": case_id,
            "fixture_hash": fixture_hash,
            "fork": "",
            "format": "",
            "json_path": case_id.split("::")[0] + ".json",
        }
        for case_id, fixture_hash in (cases or {}).items()
    ]
    return {
        "root_hash": root,
        "created_at": "2026-01-01T00:00:00Z",
        "test_count": len(test_cases),
        "forks": forks or [],
        "fixture_formats": [],
        "test_cases": test_cases,
    }


def gz_index(path: Path, index: dict) -> Path:
    """Write a gzipped index asset file."""
    path.write_bytes(gzip.compress(json.dumps(index).encode()))
    return path


def tarball_with_index(
    path: Path,
    index: dict,
    leading_member: str | None = None,
    trailing_member: bool = False,
) -> Path:
    """
    Write a small release-shaped tarball carrying the index.

    *leading_member* names a file placed before the index (a non-meta
    path there stops the recovery scan before the index is reached);
    *trailing_member* appends a fixture file after it.
    """
    with tarfile.open(path, "w:gz") as tar:

        def add(name: str, payload: bytes) -> None:
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))

        if leading_member:
            add(leading_member, b"{}")
        add("fixtures/.meta/index.json", json.dumps(index).encode())
        if trailing_member:
            add("fixtures/state_tests/a.json", b"{}")
    return path


def series_config(path: Path, fork: int, revision: int) -> Path:
    """Write a canned mainnet series configuration file."""
    path.write_text(f"fork: {fork}\nconsensus_revision: {revision}\n")
    return path


class TestPublishMainnetRelease:
    """Test publish_mainnet_release.py."""

    # Serves the notes walk: one squash commit with a tests-labeled
    # PR, one without, and a direct push carrying no PR reference,
    # spread over two pages to pin the pagination flattening.
    COMMITS = [
        {
            "sha": "1" * 40,
            "commit": {"message": "feat(tests): add foo tests (#101)\n\nbody"},
        },
        {
            "sha": "2" * 40,
            "commit": {"message": "chore(docs): tweak page (#102)"},
        },
        {
            "sha": "3" * 40,
            "commit": {"message": "Direct push without a PR"},
        },
    ]
    TAG_COMPARE_WITH_PRS = json.dumps(
        [
            {"total_commits": 3, "commits": COMMITS[:2]},
            {"total_commits": 3, "commits": COMMITS[2:]},
        ]
    )
    LABELS = {101: ["C-feat", "A-tests"], 102: ["A-doc"]}
    ROOT_AND_INDEX = {"index_root.txt": 501, "fixtures_index.json.gz": 502}

    def published(
        self,
        assets: dict[str, int] | None = None,
        published_at: str = "2026-07-01T00:00:00Z",
    ) -> str:
        """Return the canned newest published release (tests@v4.0.0)."""
        return json.dumps(
            release_json(
                12,
                "tests@v4.0.0",
                draft=False,
                asset_ids=(self.ROOT_AND_INDEX if assets is None else assets),
                published_at=published_at,
            )
        )

    def run_gate(
        self,
        tmp_path: Path,
        tags: str = "",
        releases: str = "",
        release_tag: str = "",
        text_assets: dict[int, str] | None = None,
        prev_index: dict | None = None,
        asset_files: dict[int, Path] | None = None,
        current_index: dict | None = None,
        root_hash: str = FRESH_ROOT,
        tag_compare: str = "",
        pr_labels: dict[int, list[str] | None] | None = None,
        config_fork: int = 4,
        config_revision: int = 0,
        config_text: str | None = None,
    ) -> tuple[subprocess.CompletedProcess, Path]:
        """
        Run the script with a fake `gh` on PATH; return it + summary.

        The published release canned via *release_tag* serves text
        assets from *text_assets* (the root as id 501 by convention),
        *prev_index* as the gzipped index asset id 502, and arbitrary
        binary asset files from *asset_files*. A `pr_labels` value of
        None serves a 404 for that PR number. The series configuration
        is injected via `MAINNET_VERSION_CONFIG` from *config_fork*
        and *config_revision*, or verbatim from *config_text*.
        """
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(FAKE_GH)
        fake_gh.chmod(0o755)

        index_dir = tmp_path / "index"
        index_dir.mkdir(exist_ok=True)
        current = (
            current_index
            if current_index is not None
            else index_json({}, root=root_hash)
        )
        gz_index(index_dir / "fixtures_index.json.gz", current)

        config = tmp_path / "mainnet_fixture_version.yaml"
        if config_text is None:
            series_config(config, config_fork, config_revision)
        else:
            config.write_text(config_text)

        summary = tmp_path / "summary.md"
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        env["GITHUB_REPOSITORY"] = "ethereum/execution-specs"
        env["ROOT_HASH"] = root_hash
        env["RELEASE_NOW"] = "2026-08-22T00:00:00Z"
        env["TARGET_SHA"] = "b" * 40
        env["INDEX_DIR"] = str(index_dir)
        env["MAINNET_VERSION_CONFIG"] = str(config)
        env["GITHUB_STEP_SUMMARY"] = str(summary)
        env["FAKE_GH_TAGS"] = tags
        env["FAKE_GH_RELEASES"] = releases
        env["FAKE_GH_RELEASE_TAG"] = release_tag
        env["FAKE_GH_COMPARE_TAG"] = tag_compare
        for asset_id, content in (text_assets or {}).items():
            env[f"FAKE_GH_ASSET_{asset_id}"] = content
        if prev_index is not None:
            env["FAKE_GH_ASSET_FILE_502"] = str(
                gz_index(tmp_path / "prev_index.json.gz", prev_index)
            )
        for asset_id, path in (asset_files or {}).items():
            env[f"FAKE_GH_ASSET_FILE_{asset_id}"] = str(path)
        for number, labels in (pr_labels or {}).items():
            if labels is None:
                env[f"FAKE_GH_PR_{number}"] = "__404__"
            else:
                env[f"FAKE_GH_PR_{number}"] = json.dumps(
                    {"labels": [{"name": name} for name in labels]}
                )

        result = subprocess.run(
            ["uv", "run", "-q", str(PUBLISH_MAINNET_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
        )
        return result, summary

    def publish_setup(self, current_cases: dict[str, str]) -> dict:
        """Return run_gate kwargs for a valid same-series content diff."""
        return {
            "tags": TESTS_TAGS,
            "releases": "[[]]",
            "release_tag": self.published(),
            "text_assets": {501: OLD_ROOT + "\n"},
            "prev_index": index_json({TEST_A: HASH_A}, root=OLD_ROOT),
            "current_index": index_json(current_cases, root=FRESH_ROOT),
            "tag_compare": self.TAG_COMPARE_WITH_PRS,
            "pr_labels": self.LABELS,
        }

    def test_matching_series_unchanged_root_skips(self, tmp_path):
        """Verify an unchanged root releases nothing."""
        # No index, compare or PR responses are canned, so a zero exit
        # proves neither was consulted.
        result, summary = self.run_gate(
            tmp_path,
            tags=TESTS_TAGS,
            releases="[[]]",
            release_tag=self.published({"index_root.txt": 501}),
            text_assets={501: FRESH_ROOT},
        )
        assert result.returncode == 0, result.stderr
        out = parse_matrix_output(result.stdout)
        assert out["dispatch"] == "false"
        assert "version" not in out
        assert not (tmp_path / "release_notes.md").exists()
        assert "unchanged" in summary.read_text()

    def test_patch_waits_for_fortnightly_window(self, tmp_path):
        """Verify changed content does not publish within 14 days."""
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["release_tag"] = self.published(
            published_at="2026-08-10T00:00:01Z"
        )
        # The interval gate stops before the notes walk.
        setup["tag_compare"] = ""
        setup["pr_labels"] = {}
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "once every 14 days" in summary.read_text()

    def test_patch_publishes_at_fortnightly_boundary(self, tmp_path):
        """Verify the 14-day boundary itself is eligible."""
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["release_tag"] = self.published(
            published_at="2026-08-08T00:00:00Z"
        )
        result, _ = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "true"

    def test_added_fixtures_publish(self, tmp_path):
        """Verify a pure test addition publishes the next patch."""
        result, summary = self.run_gate(
            tmp_path,
            **self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B}),
        )
        assert result.returncode == 0, result.stderr
        out = parse_matrix_output(result.stdout)
        # The scheduled gate has exactly two outputs and no draft
        # concept: publishing a validated patch is its only action.
        assert set(out) == {"dispatch", "version"}
        assert out["dispatch"] == "true"
        assert out["version"] == "v4.0.1"
        notes = (tmp_path / "release_notes.md").read_text()
        assert "tests@v4.0.1" in notes
        assert "feat(tests): add foo tests (#101)" in notes
        assert "#102" not in notes
        assert "1 added, 0 removed, 0 changed" in notes
        assert FRESH_ROOT in notes
        assert "compare/tests@v4.0.0...tests@v4.0.1" in notes
        assert "1 added, 0 removed, 0 changed" in summary.read_text()

    def test_modified_fixtures_publish(self, tmp_path):
        """Verify modified fixtures are ordinary patch content."""
        # Filler, refactor and serialization changes look exactly like
        # this: same identities, new hashes. The configured series is
        # authoritative, so no consensus semantics are inferred.
        result, summary = self.run_gate(
            tmp_path, **self.publish_setup({TEST_A: HASH_C})
        )
        assert result.returncode == 0, result.stderr
        out = parse_matrix_output(result.stdout)
        assert out["dispatch"] == "true"
        assert out["version"] == "v4.0.1"
        assert "0 added, 0 removed, 1 changed" in summary.read_text()

    def test_removed_fixtures_publish(self, tmp_path):
        """Verify a modest test removal publishes the next patch."""
        setup = self.publish_setup({TEST_A: HASH_A})
        setup["prev_index"] = index_json(
            {TEST_A: HASH_A, TEST_B: HASH_B}, root=OLD_ROOT
        )
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "true"
        assert "1 removed" in summary.read_text()

    def test_renamed_fixtures_publish_as_composite_identity(self, tmp_path):
        """Verify identity is (json_path, id): a rename adds and removes."""
        prev_case = {
            "id": TEST_A,
            "fixture_hash": HASH_A,
            "fork": "",
            "format": "",
            "json_path": "old/a.json",
        }
        setup = self.publish_setup({})
        setup["prev_index"] = index_json(raw_cases=[prev_case], root=OLD_ROOT)
        setup["current_index"] = index_json(
            raw_cases=[{**prev_case, "json_path": "new/a.json"}],
            root=FRESH_ROOT,
        )
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "true"
        assert "1 added, 1 removed, 0 changed" in summary.read_text()

    def test_consensus_revision_bump_blocks_patches(self, tmp_path):
        """
        Verify an acknowledged consensus revision awaits the manual
        release.
        """
        # Only the tag listing is canned: the gate must decide from the
        # configuration alone, before any root or index fetch, so this
        # also proves a changed root cannot slip a patch through.
        result, summary = self.run_gate(
            tmp_path, tags=TESTS_TAGS, config_revision=1
        )
        assert result.returncode == 0, result.stderr
        out = parse_matrix_output(result.stdout)
        assert out["dispatch"] == "false"
        assert "version" not in out
        text = summary.read_text()
        assert "tests@v4.1.0" in text
        assert "14-day automatic-patch window" in text

    def test_fork_bump_blocks_patches(self, tmp_path):
        """Verify an acknowledged new fork awaits the manual release."""
        result, summary = self.run_gate(
            tmp_path, tags=TESTS_TAGS, config_fork=5
        )
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "tests@v5.0.0" in summary.read_text()

    def test_published_manual_release_resumes_patch_series(self, tmp_path):
        """Verify patches resume after the new series and time window."""
        tags = json.dumps(
            [
                [{"ref": "refs/tags/tests@v4.0.0"}],
                [{"ref": "refs/tags/tests@v4.1.0"}],
            ]
        )
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["tags"] = tags
        result, _ = self.run_gate(tmp_path, config_revision=1, **setup)
        assert result.returncode == 0, result.stderr
        out = parse_matrix_output(result.stdout)
        assert out["dispatch"] == "true"
        assert out["version"] == "v4.1.1"

    def test_configured_series_behind_fails(self, tmp_path):
        """Verify a configuration behind the published series fails."""
        result, _ = self.run_gate(tmp_path, tags=TESTS_TAGS, config_fork=3)
        assert result.returncode == 1
        assert "behind" in result.stderr

    def test_skipped_consensus_revision_fails(self, tmp_path):
        """Verify a consensus revision skipping a value fails."""
        result, _ = self.run_gate(tmp_path, tags=TESTS_TAGS, config_revision=2)
        assert result.returncode == 1
        assert "skips" in result.stderr

    def test_invalid_fork_transition_fails(self, tmp_path):
        """Verify a fork skipping a value fails."""
        result, _ = self.run_gate(tmp_path, tags=TESTS_TAGS, config_fork=6)
        assert result.returncode == 1
        assert "invalid fork transition" in result.stderr

    def test_fork_bump_without_reset_fails(self, tmp_path):
        """Verify a fork bump keeping a consensus revision fails."""
        result, _ = self.run_gate(
            tmp_path, tags=TESTS_TAGS, config_fork=5, config_revision=1
        )
        assert result.returncode == 1
        assert "resetting" in result.stderr

    def test_malformed_configuration_fails(self, tmp_path):
        """Verify a malformed series configuration fails."""
        result, _ = self.run_gate(
            tmp_path, tags=TESTS_TAGS, config_text="fork: 4\n"
        )
        assert result.returncode == 1
        assert "invalid mainnet_fixture_version.yaml" in result.stderr

    def test_changed_fork_set_skips(self, tmp_path):
        """Verify a changed fork set without a fork transition skips."""
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["prev_index"] = index_json(
            {TEST_A: HASH_A}, forks=["Berlin"], root=OLD_ROOT
        )
        setup["current_index"] = index_json(
            {TEST_A: HASH_A, TEST_B: HASH_B},
            forks=["Berlin", "Osaka"],
            root=FRESH_ROOT,
        )
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "fork set" in summary.read_text()

    def test_mass_removal_skips(self, tmp_path):
        """Verify a mass test disappearance releases nothing."""
        prev = {f"tests/t.py::t[{i}]": HASH_A for i in range(1200)}
        setup = self.publish_setup(dict(list(prev.items())[:100]))
        setup["prev_index"] = index_json(prev, root=OLD_ROOT)
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "vanished" in summary.read_text()

    def test_duplicate_identities_in_current_index_fail(self, tmp_path):
        """Verify a duplicate identity in this run's index fails."""
        case = {
            "id": TEST_A,
            "fixture_hash": HASH_A,
            "fork": "",
            "format": "",
            "json_path": "a.json",
        }
        setup = self.publish_setup({})
        setup["current_index"] = index_json(
            raw_cases=[case, dict(case)], root=FRESH_ROOT
        )
        result, _ = self.run_gate(tmp_path, **setup)
        assert result.returncode == 1
        assert "duplicate fixture identities" in result.stderr

    def test_duplicate_identities_in_prev_index_skip(self, tmp_path):
        """Verify a duplicate identity in the previous index skips."""
        case = {
            "id": TEST_A,
            "fixture_hash": HASH_A,
            "fork": "",
            "format": "",
            "json_path": "a.json",
        }
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["prev_index"] = index_json(
            raw_cases=[case, dict(case)], root=OLD_ROOT
        )
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "duplicate" in summary.read_text()

    def test_root_equality_via_the_index_asset(self, tmp_path):
        """Verify a release without a root asset still compares roots."""
        result, summary = self.run_gate(
            tmp_path,
            tags=TESTS_TAGS,
            releases="[[]]",
            release_tag=self.published({"fixtures_index.json.gz": 502}),
            prev_index=index_json({TEST_A: HASH_A}, root=FRESH_ROOT),
            current_index=index_json({TEST_A: HASH_A}, root=FRESH_ROOT),
        )
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "unchanged" in summary.read_text()

    def test_legacy_tarball_with_leading_ini_recovers(self, tmp_path):
        """Verify metadata files before the index do not stop recovery."""
        tar = tarball_with_index(
            tmp_path / "prev.tar.gz",
            index_json({TEST_A: HASH_A}, root=OLD_ROOT),
            leading_member="fixtures/.meta/fixtures.ini",
            trailing_member=True,
        )
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["release_tag"] = self.published(
            {"index_root.txt": 501, "fixtures.tar.gz": 500}
        )
        setup.pop("prev_index")
        setup["asset_files"] = {500: tar}
        result, _ = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        out = parse_matrix_output(result.stdout)
        assert out["dispatch"] == "true"
        assert out["version"] == "v4.0.1"

    def test_tarball_without_metadata_index_skips(self, tmp_path):
        """Verify a tarball whose index is not in early metadata skips."""
        tar = tarball_with_index(
            tmp_path / "prev.tar.gz",
            index_json({TEST_A: HASH_A}, root=OLD_ROOT),
            leading_member="fixtures/state_tests/a.json",
        )
        setup = self.publish_setup({TEST_A: HASH_A})
        setup["release_tag"] = self.published(
            {"index_root.txt": 501, "fixtures.tar.gz": 500}
        )
        setup.pop("prev_index")
        setup["asset_files"] = {500: tar}
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "could not be recovered" in summary.read_text()

    def test_corrupt_index_asset_falls_back_to_the_tarball(self, tmp_path):
        """Verify a corrupt index asset falls back to the tarball."""
        garbage = tmp_path / "garbage.gz"
        garbage.write_bytes(b"not gzip at all")
        tar = tarball_with_index(
            tmp_path / "prev.tar.gz",
            index_json({TEST_A: HASH_A}, root=OLD_ROOT),
        )
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["release_tag"] = self.published(
            {
                "index_root.txt": 501,
                "fixtures_index.json.gz": 502,
                "fixtures.tar.gz": 500,
            }
        )
        setup.pop("prev_index")
        setup["asset_files"] = {502: garbage, 500: tar}
        result, _ = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "true"

    def test_unrecoverable_prev_index_skips(self, tmp_path):
        """Verify an unvalidatable content difference releases nothing."""
        setup = self.publish_setup({TEST_A: HASH_A})
        setup["release_tag"] = self.published({"index_root.txt": 501})
        setup.pop("prev_index")
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "could not be recovered" in summary.read_text()

    def test_deleted_release_behind_the_tag_skips(self, tmp_path):
        """Verify a tag whose release was deleted skips, not crashes."""
        setup = self.publish_setup({TEST_A: HASH_A})
        setup["release_tag"] = "__404__"
        setup.pop("prev_index")
        setup.pop("text_assets")
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "could not be recovered" in summary.read_text()

    def test_capped_compare_listing_skips(self, tmp_path):
        """Verify an API-capped commit listing releases nothing."""
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["tag_compare"] = json.dumps(
            [{"total_commits": 5, "commits": self.COMMITS}]
        )
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "capped" in summary.read_text()

    def test_pending_next_patch_draft_blocks(self, tmp_path):
        """Verify a pending draft of the next patch version blocks."""
        # The draft sits on the second page to pin the pagination
        # flattening.
        releases = json.dumps([[], [release_json(77, "tests@v4.0.1")]])
        result, summary = self.run_gate(
            tmp_path, tags=TESTS_TAGS, releases=releases
        )
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "awaiting publish" in summary.read_text()

    def test_higher_version_draft_blocks(self, tmp_path):
        """Verify a pending manual release draft blocks."""
        releases = json.dumps([[release_json(88, "tests@v4.1.0")]])
        result, summary = self.run_gate(
            tmp_path, tags=TESTS_TAGS, releases=releases
        )
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "awaiting publish" in summary.read_text()

    def test_older_and_published_entries_do_not_block(self, tmp_path):
        """Verify drafts at or below the published version are ignored."""
        releases = json.dumps(
            [
                [
                    # A cached-release test dispatch's leftover draft.
                    release_json(11, "tests@v0.0.913"),
                    # A published release, a re-draft at the published
                    # version and another feature's draft.
                    release_json(12, "tests@v4.0.0", draft=False),
                    release_json(14, "tests@v4.0.0"),
                    release_json(13, "tests-bal@v99.0.0"),
                ]
            ]
        )
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["releases"] = releases
        result, _ = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        out = parse_matrix_output(result.stdout)
        assert out["dispatch"] == "true"
        assert out["version"] == "v4.0.1"

    def test_numeric_version_ordering(self, tmp_path):
        """Verify the newest tag is picked numerically, not textually."""
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["tags"] = json.dumps(
            [
                [{"ref": "refs/tags/tests@v9.0.0"}],
                [{"ref": "refs/tags/tests@v10.0.0"}],
            ]
        )
        result, _ = self.run_gate(tmp_path, config_fork=10, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["version"] == "v10.0.1"

    def test_dangling_pr_reference_is_skipped(self, tmp_path):
        """Verify a subject referencing a non-PR does not fail the gate."""
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["pr_labels"] = {101: None, 102: ["A-doc"]}
        result, summary = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "true"
        assert "No merged" in summary.read_text()

    def test_no_labeled_prs_still_publishes(self, tmp_path):
        """Verify a content change without tests labels still releases."""
        setup = self.publish_setup({TEST_A: HASH_A, TEST_B: HASH_B})
        setup["pr_labels"] = {101: ["C-feat"], 102: ["A-doc"]}
        result, _ = self.run_gate(tmp_path, **setup)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "true"
        notes = (tmp_path / "release_notes.md").read_text()
        assert "None." in notes
        assert "#101" not in notes

    def test_no_published_tag_skips(self, tmp_path):
        """Verify a repo without a `tests@` tag skips the release."""
        result, summary = self.run_gate(tmp_path, tags=NO_TAGS)
        assert result.returncode == 0, result.stderr
        assert parse_matrix_output(result.stdout)["dispatch"] == "false"
        assert "manually" in summary.read_text()

    def test_empty_root_hash_fails(self, tmp_path):
        """Verify a missing merged index root fails loudly."""
        result, _ = self.run_gate(tmp_path, root_hash="")
        assert result.returncode == 1
        assert "ROOT_HASH" in result.stderr


class TestValidateMainnetRelease:
    """Test validate_mainnet_release.py."""

    def run_validate(
        self,
        tmp_path: Path,
        version: str,
        tags: str = TESTS_TAGS,
        config_fork: int = 4,
        config_revision: int = 0,
        cached_target_series: tuple[int, int] | None = None,
        cached_target_missing: bool = False,
    ) -> subprocess.CompletedProcess:
        """Run the validator with a fake `gh` on PATH."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(FAKE_GH)
        fake_gh.chmod(0o755)

        config = series_config(
            tmp_path / "mainnet_fixture_version.yaml",
            config_fork,
            config_revision,
        )
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        env["GITHUB_REPOSITORY"] = "ethereum/execution-specs"
        env["INPUT_VERSION"] = version
        env["MAINNET_VERSION_CONFIG"] = str(config)
        env["FAKE_GH_TAGS"] = tags
        if cached_target_series is not None or cached_target_missing:
            env["CACHED_TARGET_SHA"] = "c" * 40
            if cached_target_missing:
                env["FAKE_GH_SERIES_CONFIG"] = "__404__"
            else:
                assert cached_target_series is not None
                target_text = (
                    f"fork: {cached_target_series[0]}\n"
                    f"consensus_revision: {cached_target_series[1]}\n"
                )
                env["FAKE_GH_SERIES_CONFIG"] = json.dumps(
                    {
                        "content": base64.b64encode(
                            target_text.encode()
                        ).decode()
                    }
                )
        return subprocess.run(
            ["uv", "run", "-q", str(VALIDATE_MAINNET_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
        )

    def test_same_series_patch_allowed(self, tmp_path):
        """Verify a forward patch of the published series passes."""
        result = self.run_validate(tmp_path, "v4.0.1")
        assert result.returncode == 0, result.stderr

    def test_same_series_backward_rejected(self, tmp_path):
        """Verify a version at or below the newest release is rejected."""
        result = self.run_validate(tmp_path, "v4.0.0")
        assert result.returncode == 1
        assert "greater" in result.stderr

    def test_configured_consensus_release_allowed(self, tmp_path):
        """Verify the configured consensus release version passes."""
        result = self.run_validate(tmp_path, "v4.1.0", config_revision=1)
        assert result.returncode == 0, result.stderr

    def test_configured_fork_release_allowed(self, tmp_path):
        """Verify the configured new-fork release version passes."""
        result = self.run_validate(tmp_path, "v5.0.0", config_fork=5)
        assert result.returncode == 0, result.stderr

    def test_cached_new_series_requires_matching_nightly(self, tmp_path):
        """Verify a new-series release accepts a matching cached fill."""
        result = self.run_validate(
            tmp_path,
            "v4.1.0",
            config_revision=1,
            cached_target_series=(4, 1),
        )
        assert result.returncode == 0, result.stderr

    def test_cached_new_series_rejects_stale_nightly(self, tmp_path):
        """Verify pre-consensus cached fixtures cannot start a series."""
        result = self.run_validate(
            tmp_path,
            "v4.1.0",
            config_revision=1,
            cached_target_series=(4, 0),
        )
        assert result.returncode == 1
        assert "not the required 4.1" in result.stderr

    def test_cached_new_series_rejects_pre_config_nightly(self, tmp_path):
        """Verify a nightly predating the series file cannot be reused."""
        result = self.run_validate(
            tmp_path,
            "v4.1.0",
            config_revision=1,
            cached_target_missing=True,
        )
        assert result.returncode == 1
        assert "predates mainnet_fixture_version.yaml" in result.stderr

    def test_new_series_without_configuration_rejected(self, tmp_path):
        """Verify a new series needs the configuration updated first."""
        result = self.run_validate(tmp_path, "v4.1.0")
        assert result.returncode == 1
        assert "mainnet_fixture_version.yaml" in result.stderr

    def test_wrong_new_series_version_rejected(self, tmp_path):
        """Verify a new-series version must exactly match `vX.Y.0`."""
        result = self.run_validate(tmp_path, "v4.1.1", config_revision=1)
        assert result.returncode == 1
        assert "exactly" in result.stderr
        result = self.run_validate(tmp_path, "v5.0.0", config_revision=1)
        assert result.returncode == 1
        assert "exactly" in result.stderr

    def test_invalid_configuration_rejected(self, tmp_path):
        """Verify an invalid configured transition is rejected."""
        result = self.run_validate(tmp_path, "v4.2.0", config_revision=2)
        assert result.returncode == 1
        assert "skips" in result.stderr

    def test_first_release_allowed(self, tmp_path):
        """Verify any first release passes with no published tag."""
        result = self.run_validate(tmp_path, "v1.0.0", tags=NO_TAGS)
        assert result.returncode == 0, result.stderr
