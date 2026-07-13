"""
Test the CI release helper scripts.

Each test invokes the script via `uv run` to validate the actual CLI
interface, matching how GitHub Actions calls them.
"""

import json
import os
import subprocess
import tarfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent
REPO_ROOT = SCRIPTS_DIR.parent.parent

BUILD_MATRIX_SCRIPT = SCRIPTS_DIR / "generate_build_matrix.py"
TARBALL_SCRIPT = SCRIPTS_DIR / "create_release_tarball.py"
MERGE_INDEX_SCRIPT = SCRIPTS_DIR / "merge_index_files.py"
CHECK_COMMITS_SCRIPT = SCRIPTS_DIR / "check_new_commits.py"


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


# Fake `gh` served from PATH: answers the two API calls the commit-check
# script makes with canned JSON from env vars, and fails loudly on any
# other (or unconfigured) call.
FAKE_GH = """#!/usr/bin/env bash
case "$2" in
  *actions/workflows*) response="$FAKE_GH_RUNS" ;;
  *compare*) response="$FAKE_GH_COMPARE" ;;
  *) response="" ;;
esac
if [ -z "$response" ]; then
  echo "unexpected gh call: $*" >&2
  exit 1
fi
printf '%s' "$response"
"""


class TestCheckNewCommits:
    """Test check_new_commits.py."""

    def run_check(
        self,
        tmp_path: Path,
        event_name: str,
        runs: str = "",
        compare: str = "",
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

    def test_schedule_with_new_commits_runs(self, tmp_path):
        """Verify new commits since the baseline trigger a run."""
        commit = {
            "sha": "abcdef1" + "0" * 33,
            "commit": {"message": "feat(x): subject\n\nbody"},
        }
        result, summary = self.run_check(
            tmp_path,
            "schedule",
            runs=json.dumps({"workflow_runs": [{"head_sha": "a" * 40}]}),
            compare=json.dumps({"commits": [commit]}),
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "run=true"
        text = summary.read_text()
        assert "### Commits since last successful nightly fill" in text
        # Short SHA plus the commit subject, without the body.
        assert "- abcdef1 feat(x): subject" in text
        assert "body" not in text

    def test_schedule_without_new_commits_skips(self, tmp_path):
        """Verify no commits since the baseline skips the run."""
        result, summary = self.run_check(
            tmp_path,
            "schedule",
            runs=json.dumps({"workflow_runs": [{"head_sha": "b" * 40}]}),
            compare=json.dumps({"commits": []}),
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "run=false"
        assert "skipping" in summary.read_text()

    def test_gh_failure_fails_the_check(self, tmp_path):
        """Verify a failing `gh` call fails the script."""
        result, _ = self.run_check(tmp_path, "schedule")
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
