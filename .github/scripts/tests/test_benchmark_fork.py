"""Check that the benchmark fork is defined consistently."""

import re
import subprocess
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parents[3]
FEATURE_CONFIG = REPO_ROOT / ".github" / "configs" / "feature.yaml"


def test_feature_config_uses_justfile_benchmark_fork() -> None:
    """Verify benchmark releases fill the Justfile's `benchmark_fork`."""
    benchmark_fork = subprocess.run(
        ["just", "--evaluate", "benchmark_fork"],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    ).stdout.strip()
    features = yaml.safe_load(FEATURE_CONFIG.read_text())
    benchmark_features = {
        name: feature
        for name, feature in features.items()
        if feature.get("evm-type") == "benchmark"
    }
    assert benchmark_features, "no benchmark features in feature.yaml"
    for name, feature in benchmark_features.items():
        forks = re.findall(r"--fork[= ](\S+)", feature["fill-params"])
        assert forks == [benchmark_fork], (
            f"feature.yaml '{name}' fills {forks}, but the Justfile's "
            f"benchmark_fork is {benchmark_fork!r}; keep them in sync"
        )
