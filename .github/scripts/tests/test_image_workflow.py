"""Exercise image publication guards and manual nightly artifact lookup."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/docker-images.yaml"
RESOLVER = ROOT / ".github/scripts/resolve_image_nightly.py"
SHA = "a" * 40
REPOSITORY = "danceratopz/execution-specs"


@pytest.mark.parametrize(
    "event,branch,head,expected",
    [
        ("push", "forks/amsterdam", SHA, "true"),
        ("push", "forks/amsterdam", "b" * 40, "false"),
        ("push", "devnets/glamsterdam/8", "b" * 40, "false"),
        ("release", "tests@v20.0.2", "", "true"),
        ("workflow_dispatch", "forks/amsterdam", "", "true"),
        ("schedule", "forks/amsterdam", "", "true"),
    ],
)
def test_superseded_push_guard(tmp_path, event, branch, head, expected):
    """Skip stale pushes without cancelling releases or manual rebuilds."""
    workflow = yaml.safe_load(WORKFLOW.read_text())
    step = next(
        s
        for s in workflow["jobs"]["plan"]["steps"]
        if s.get("id") == "current"
    )
    git = tmp_path / "git"
    # Non-push events must not attempt to resolve a branch, including the
    # release event whose GITHUB_REF_NAME is a tag rather than a branch.
    git.write_text(
        "#!/bin/sh\n"
        'test -n "$FAKE_HEAD" || exit 1\n'
        'printf "%s\\t%s\\n" "$FAKE_HEAD" "$4"\n'
    )
    git.chmod(0o755)
    output = tmp_path / "output"
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", step["run"]],
        env={
            **os.environ,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "EVENT": event,
            "GITHUB_SHA": SHA,
            "GITHUB_REF_NAME": branch,
            "FAKE_HEAD": head,
            "GITHUB_OUTPUT": str(output),
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_text() == f"build={expected}\n"


def resolve(tmp_path, *, runs, artifacts, commit=SHA[:7]):
    """Invoke the real resolver against a deterministic GitHub API stub."""
    responses = {
        f"repos/{REPOSITORY}/commits/{commit}": {"sha": SHA},
        f"repos/{REPOSITORY}/actions/workflows/release_fixtures.yaml"
        f"/runs?event=schedule&status=completed&head_sha={SHA}"
        "&per_page=100": runs,
        **{
            f"repos/{REPOSITORY}/actions/runs/{run_id}"
            "/artifacts?per_page=100": pages
            for run_id, pages in artifacts.items()
        },
    }
    api = tmp_path / "api.json"
    api.write_text(json.dumps(responses))
    gh = tmp_path / "gh"
    gh.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "data = json.load(open(os.environ['FAKE_API']))\n"
        "print(json.dumps(data[sys.argv[-1]]))\n"
    )
    gh.chmod(0o755)
    return subprocess.run(
        [sys.executable, str(RESOLVER)],
        env={
            **os.environ,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "GITHUB_REPOSITORY": REPOSITORY,
            "INPUT_COMMIT": commit,
            "FAKE_API": str(api),
        },
        capture_output=True,
        text=True,
    )


def test_resolve_fill_after_publication_failed(tmp_path):
    """Reuse the exact live fill across pages despite a failed image job."""
    result = resolve(
        tmp_path,
        runs=[
            {"workflow_runs": [{"id": 3, "head_sha": SHA}]},
            {
                "workflow_runs": [
                    {"id": 2, "head_sha": SHA, "conclusion": "failure"}
                ]
            },
        ],
        artifacts={
            3: [{"artifacts": []}],
            2: [
                {
                    "artifacts": [
                        {"name": "fixtures_bbbbbbb", "expired": False}
                    ]
                },
                {
                    "artifacts": [
                        {"name": "fixtures_aaaaaaa", "expired": False}
                    ]
                },
            ],
        },
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["run_id=2", f"target_sha={SHA}"]


@pytest.mark.parametrize(
    "artifacts",
    [
        [],
        [{"name": "fixtures_aaaaaaa", "expired": True}],
        [{"name": "fixtures_bbbbbbb", "expired": False}],
    ],
)
def test_missing_live_artifact_fails(tmp_path, artifacts):
    """Never publish using an expired, absent or different fill artifact."""
    result = resolve(
        tmp_path,
        runs=[{"workflow_runs": [{"id": 2, "head_sha": SHA}]}],
        artifacts={2: [{"artifacts": artifacts}]},
    )
    assert result.returncode == 1
    assert "no completed scheduled fill" in result.stderr
    assert not result.stdout


def test_invalid_commit_fails_before_lookup(tmp_path):
    """Reject branch names where the manual nightly input promises a SHA."""
    result = resolve(tmp_path, runs=[], artifacts={}, commit="forks/amsterdam")
    assert result.returncode == 1
    assert "7 to 40 lowercase hex" in result.stderr


def test_other_commit_is_not_reused(tmp_path):
    """Reject a run from another commit even if it has a matching artifact."""
    result = resolve(
        tmp_path,
        runs=[{"workflow_runs": [{"id": 2, "head_sha": "b" * 40}]}],
        artifacts={},
    )
    assert result.returncode == 1
    assert "no completed scheduled fill" in result.stderr


PUSH_TAGS = ROOT / ".github/scripts/push_image_tags.sh"
IMAGE = "ghcr.io/ethereum/execution-specs/hive/consume-engine"


def push_tags(tmp_path, *, tags, immutable, existing=(), error="not found"):
    """Run the push helper against a docker stub that records its calls."""
    docker = tmp_path / "bin" / "docker"
    docker.parent.mkdir()
    docker.write_text(
        f"#!{sys.executable}\n"
        "import os, sys\n"
        "log = os.environ['FAKE_LOG']\n"
        "args = sys.argv[1:]\n"
        "pushed = open(log).read().split() if os.path.exists(log) else []\n"
        "if args[:3] == ['buildx', 'imagetools', 'inspect']:\n"
        "    ref = args[3]\n"
        "    if ref in os.environ['FAKE_EXISTING'].split() or ref in pushed:\n"
        "        print('sha256:' + 'd' * 64)\n"
        "        sys.exit(0)\n"
        "    sys.exit(f\"ERROR: {ref}: {os.environ['FAKE_ERROR']}\")\n"
        "if args[0] == 'push':\n"
        "    open(log, 'a').write(args[1] + '\\n')\n"
    )
    docker.chmod(0o755)
    log = tmp_path / "pushed"
    result = subprocess.run(
        [
            str(PUSH_TAGS),
            f"{IMAGE}:local",
            IMAGE,
            " ".join(tags),
            immutable,
            SHA,
            "tests@v20.0.2",
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": f"{docker.parent}:{os.environ['PATH']}",
            "FAKE_LOG": str(log),
            "FAKE_EXISTING": " ".join(f"{IMAGE}:{tag}" for tag in existing),
            "FAKE_ERROR": error,
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
        },
        capture_output=True,
        text=True,
    )
    pushed = log.read_text().split() if log.exists() else []
    digests = list((tmp_path / "digests").glob("*.json"))
    recorded = json.loads(digests[0].read_text())["tags"] if digests else []
    return result, [ref.rpartition(":")[2] for ref in pushed], recorded


@pytest.mark.parametrize(
    "tags,immutable,existing,pushed",
    [
        # A release run publishes its release tag once.
        (["v20.0.2", "latest"], "v20.0.2", [], ["v20.0.2", "latest"]),
        # A re-run keeps the published release tag; the channel moves.
        (["v20.0.2", "latest"], "v20.0.2", ["v20.0.2"], ["latest"]),
        # A push moves only its channel, which is never immutable.
        (["latest"], "", ["latest"], ["latest"]),
        # A re-run of an older release publishes nothing.
        (["v20.0.1"], "v20.0.1", ["v20.0.1"], []),
    ],
)
def test_release_tags_are_not_overwritten(
    tmp_path, tags, immutable, existing, pushed
):
    """Skip an existing release tag; push and record every other tag."""
    result, actual, recorded = push_tags(
        tmp_path, tags=tags, immutable=immutable, existing=existing
    )
    assert result.returncode == 0, result.stderr
    assert actual == pushed
    assert recorded == pushed


def test_registry_error_fails_before_pushing(tmp_path):
    """Only a missing tag counts as unpublished; other errors fail the run."""
    result, pushed, _ = push_tags(
        tmp_path,
        tags=["v20.0.2", "latest"],
        immutable="v20.0.2",
        error="unexpected status: 500 Internal Server Error",
    )
    assert result.returncode != 0
    assert pushed == []
