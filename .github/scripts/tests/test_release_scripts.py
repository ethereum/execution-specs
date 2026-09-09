"""
Test the CI release helper scripts.

Each test invokes the script via `uv run` to validate the actual CLI
interface, matching how GitHub Actions calls them.
"""

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
CHECK_ZKEVM_RELEASE_SCRIPT = SCRIPTS_DIR / "check_zkevm_benchmark_release.py"
RESOLVE_GIT_REF_SCRIPT = SCRIPTS_DIR / "resolve_git_ref.py"
VALIDATE_ZKEVM_FIXTURES_SCRIPT = (
    SCRIPTS_DIR / "validate_zkevm_benchmark_fixtures.py"
)


def run_script(
    script: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    """Run a uv inline-deps script and return the result."""
    return subprocess.run(
        ["uv", "run", "-q", str(script), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
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

    def test_zkevm_benchmark_produces_single_entry(self):
        """Verify the zkEVM benchmark feature is an unsplit build."""
        result = run_script(
            BUILD_MATRIX_SCRIPT,
            "zkevm-benchmark",
            "v0.9.0",
        )
        assert result.returncode == 0
        out = parse_matrix_output(result.stdout)
        matrix = json.loads(out["build_matrix"])
        assert matrix == [
            {
                "feature": "zkevm-benchmark",
                "label": "",
                "from_fork": "",
                "until_fork": "",
            }
        ]

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


# Fake `gh` served from PATH: answers the API calls the commit-check
# and cached-release scripts make with canned JSON from env vars, and
# fails loudly on any other (or unconfigured) call. The API path is
# the last argument (flags such as `--paginate --slurp` may precede
# it). Per-run artifact responses come from
# `FAKE_GH_ARTIFACTS_<run_id>`, falling back to `FAKE_GH_ARTIFACTS`.
FAKE_GH = """#!/usr/bin/env bash
path="${@: -1}"
case "$path" in
  *actions/workflows*) response="$FAKE_GH_RUNS" ;;
  *matching-refs/tags/tests-zkevm-benchmark*)
    response="${FAKE_GH_DESTINATION_TAGS:-$FAKE_GH_TAGS}"
    ;;
  */artifacts)
    run_id="${path##*/runs/}"
    run_id="${run_id%%/*}"
    var="FAKE_GH_ARTIFACTS_${run_id}"
    response="${!var:-$FAKE_GH_ARTIFACTS}"
    ;;
  *matching-refs*) response="$FAKE_GH_TAGS" ;;
  *releases*) response="$FAKE_GH_RELEASES" ;;
  *compare/tests@*) response="$FAKE_GH_COMPARE_TAG" ;;
  *compare*) response="$FAKE_GH_COMPARE" ;;
  *) response="" ;;
esac
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


class TestResolveGitRef:
    """Test resolve_git_ref.py."""

    def run_with_fake_git(
        self, tmp_path: Path, ref: str, output: str, exit_code: int
    ) -> subprocess.CompletedProcess:
        """Run the resolver with a fake git command."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        fake_git = bin_dir / "git"
        fake_git.write_text(
            f"#!/usr/bin/env bash\nprintf '%s' '{output}'\nexit {exit_code}\n"
        )
        fake_git.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        return run_script(
            RESOLVE_GIT_REF_SCRIPT,
            "example/geth",
            ref,
            env=env,
        )

    def test_full_commit_does_not_query_remote(self):
        """Verify a full commit SHA resolves without a git command."""
        commit = "a" * 40
        result = run_script(RESOLVE_GIT_REF_SCRIPT, "example/geth", commit)
        assert result.returncode == 0
        assert result.stdout.strip() == commit

    def test_branch_resolves_to_full_commit(self, tmp_path):
        """Verify a branch uses the commit returned by git ls-remote."""
        commit = "b" * 40
        result = self.run_with_fake_git(
            tmp_path,
            "devnet",
            f"{commit}\trefs/heads/devnet\n",
            0,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == commit

    def test_unresolved_branch_fails(self, tmp_path):
        """Verify an unresolved branch stops the build."""
        result = self.run_with_fake_git(tmp_path, "missing", "", 2)
        assert result.returncode == 1
        assert "could not resolve branch 'missing'" in result.stderr

    def test_empty_ref_fails(self):
        """Verify an empty ref stops the build."""
        result = run_script(RESOLVE_GIT_REF_SCRIPT, "example/geth", "")
        assert result.returncode == 1
        assert "ref is empty" in result.stderr


class TestCheckZkevmBenchmarkRelease:
    """Test check_zkevm_benchmark_release.py."""

    @staticmethod
    def run_check(
        tmp_path: Path,
        destination_tags: str = "[[]]",
        releases: str = "[[]]",
        version: str = "v0.9.0",
        source_ref: str = "tests-zkevm@v0.9.0",
    ) -> subprocess.CompletedProcess:
        """Run the release check with canned GitHub API responses."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(FAKE_GH)
        fake_gh.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        env["GITHUB_REPOSITORY"] = "ethereum/execution-specs"
        env["FAKE_GH_DESTINATION_TAGS"] = destination_tags
        env["FAKE_GH_RELEASES"] = releases
        return run_script(
            CHECK_ZKEVM_RELEASE_SCRIPT,
            version,
            source_ref,
            env=env,
        )

    def test_new_release_request_passes(self, tmp_path):
        """Verify a matching source input and unused destination pass."""
        result = self.run_check(tmp_path)
        assert result.returncode == 0
        assert "Destination release: tests-zkevm-benchmark@v0.9.0" in (
            result.stdout
        )

    def test_existing_destination_tag_fails(self, tmp_path):
        """Verify an existing destination tag stops the request."""
        destination_tags = json.dumps(
            [[{"ref": "refs/tags/tests-zkevm-benchmark@v0.9.0"}]]
        )
        result = self.run_check(tmp_path, destination_tags=destination_tags)
        assert result.returncode == 1
        assert "destination tag" in result.stderr

    def test_existing_destination_draft_fails(self, tmp_path):
        """Verify an existing destination draft stops the request."""
        releases = json.dumps(
            [[{"tag_name": "tests-zkevm-benchmark@v0.9.0", "draft": True}]]
        )
        result = self.run_check(tmp_path, releases=releases)
        assert result.returncode == 1
        assert "release or draft" in result.stderr

    def test_mismatched_source_ref_fails_without_api_call(self, tmp_path):
        """Verify the source ref and release version must match."""
        result = self.run_check(
            tmp_path,
            source_ref="tests-zkevm@v0.8.0",
        )
        assert result.returncode == 1
        assert "source ref must be 'tests-zkevm@v0.9.0'" in result.stderr


class TestValidateZkevmBenchmarkFixtures:
    """Test validate_zkevm_benchmark_fixtures.py."""

    fixture_path = (
        "fixtures/blockchain_tests/for_amsterdam_at_0060M/"
        "benchmark/compute/test_example.json"
    )

    @staticmethod
    def valid_fixture() -> dict:
        """Return one valid zkEVM benchmark fixture file."""
        return {
            "test_example": {
                "network": "Amsterdam",
                "blocks": [
                    {
                        "statelessInputBytes": "0x1234",
                        "statelessOutputBytes": "0xabcd",
                    }
                ],
                "_info": {
                    "metadata": {
                        "opcode_count_per_block": [{"ADD": 1}],
                    }
                },
            }
        }

    @staticmethod
    def make_archive(tmp_path: Path, files: dict[str, dict]) -> Path:
        """Create a fixture archive from JSON file mappings."""
        archive_path = tmp_path / "fixtures_zkevm-benchmark.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            for name, contents in files.items():
                data = json.dumps(contents).encode()
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
        return archive_path

    def run_validator(
        self, tmp_path: Path, files: dict[str, dict]
    ) -> subprocess.CompletedProcess:
        """Create and validate one fixture archive."""
        archive_path = self.make_archive(tmp_path, files)
        return run_script(VALIDATE_ZKEVM_FIXTURES_SCRIPT, str(archive_path))

    def test_valid_archive_passes(self, tmp_path):
        """Verify an archive with all configured gas limits passes."""
        files = {
            self.fixture_path.replace("0060M", gas_limit): self.valid_fixture()
            for gas_limit in ("0010M", "0030M", "0060M")
        }
        result = self.run_validator(tmp_path, files)
        assert result.returncode == 0
        assert "Validated 3 fixture cases in 3 fixture files" in result.stdout

    def test_empty_archive_fails(self, tmp_path):
        """Verify an empty archive fails."""
        result = self.run_validator(tmp_path, {})
        assert result.returncode == 1
        assert "contains no zkEVM benchmark fixtures" in result.stderr

    def test_wrong_target_directory_fails(self, tmp_path):
        """Verify fixtures must use a configured gas limit."""
        path = self.fixture_path.replace("0060M", "0050M")
        result = self.run_validator(tmp_path, {path: self.valid_fixture()})
        assert result.returncode == 1
        assert "target must be one of" in result.stderr

    def test_wrong_fork_directory_fails(self, tmp_path):
        """Verify fixtures cannot target another fork."""
        path = self.fixture_path.replace("amsterdam", "prague")
        result = self.run_validator(tmp_path, {path: self.valid_fixture()})
        assert result.returncode == 1
        assert "target must be one of" in result.stderr

    def test_extra_fixture_format_fails(self, tmp_path):
        """Verify the archive cannot contain another fixture format."""
        engine_path = (
            "fixtures/blockchain_tests_engine/for_amsterdam_at_0060M/"
            "benchmark/compute/test_example.json"
        )
        result = self.run_validator(
            tmp_path,
            {
                self.fixture_path: self.valid_fixture(),
                engine_path: self.valid_fixture(),
            },
        )
        assert result.returncode == 1
        assert "unexpected fixture formats" in result.stderr

    def test_missing_stateless_input_fails(self, tmp_path):
        """Verify the final block must contain stateless input bytes."""
        fixture = self.valid_fixture()
        del fixture["test_example"]["blocks"][-1]["statelessInputBytes"]
        result = self.run_validator(tmp_path, {self.fixture_path: fixture})
        assert result.returncode == 1
        assert "statelessInputBytes must be" in result.stderr

    def test_malformed_stateless_output_fails(self, tmp_path):
        """Verify the final block output must contain complete bytes."""
        fixture = self.valid_fixture()
        fixture["test_example"]["blocks"][-1]["statelessOutputBytes"] = "0x1"
        result = self.run_validator(tmp_path, {self.fixture_path: fixture})
        assert result.returncode == 1
        assert "statelessOutputBytes must be" in result.stderr

    def test_empty_blocks_fails(self, tmp_path):
        """Verify each fixture case must contain a block."""
        fixture = self.valid_fixture()
        fixture["test_example"]["blocks"] = []
        result = self.run_validator(tmp_path, {self.fixture_path: fixture})
        assert result.returncode == 1
        assert "blocks must be a non-empty list" in result.stderr

    def test_opcode_count_length_must_match_blocks(self, tmp_path):
        """Verify opcode count metadata has one entry for each block."""
        fixture = self.valid_fixture()
        metadata = fixture["test_example"]["_info"]["metadata"]
        metadata["opcode_count_per_block"] = []
        result = self.run_validator(tmp_path, {self.fixture_path: fixture})
        assert result.returncode == 1
        assert "has 0 entries for 1 blocks" in result.stderr

    def test_opcode_count_metadata_is_required(self, tmp_path):
        """Verify each fixture case contains opcode count metadata."""
        fixture = self.valid_fixture()
        del fixture["test_example"]["_info"]["metadata"]
        result = self.run_validator(tmp_path, {self.fixture_path: fixture})
        assert result.returncode == 1
        assert "opcode_count_per_block must be a list" in result.stderr

    def test_final_opcode_count_must_not_be_empty(self, tmp_path):
        """Verify the final opcode count contains at least one opcode."""
        fixture = self.valid_fixture()
        metadata = fixture["test_example"]["_info"]["metadata"]
        metadata["opcode_count_per_block"] = [{}]
        result = self.run_validator(tmp_path, {self.fixture_path: fixture})
        assert result.returncode == 1
        assert "final opcode count must be a non-empty object" in result.stderr


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
