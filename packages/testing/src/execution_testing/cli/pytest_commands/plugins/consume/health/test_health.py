"""Health check tests for consume direct client binaries."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

from execution_testing.client_clis.fixture_consumer_tool import (
    FixtureConsumerTool,
)
from execution_testing.fixtures import (
    BlockchainEngineFixture,
    BlockchainFixture,
    StateFixture,
)

CONFIG_FILE = "consume-direct.toml"

SANITY_DIR = Path(__file__).parent.parent / "direct" / "sanity_fixtures"

FORMAT_MAP = {
    "state": StateFixture,
    "block": BlockchainFixture,
    "engine": BlockchainEngineFixture,
}

TYPE_TO_SUBDIR = {
    "state": "state_tests",
    "block": "blockchain_tests",
    "engine": "blockchain_tests_engine",
}


def load_config() -> Dict[str, Dict[str, str]]:
    config_path = Path.cwd() / CONFIG_FILE
    if not config_path.exists():
        pytest.skip(
            f"{CONFIG_FILE} not found. "
            f"Run `consume direct health` to create it."
        )
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def detect_version(bin_path: Path) -> Optional[str]:
    """Detect version from a binary or dotnet project."""
    is_dotnet = (
        bin_path.is_dir()
        or bin_path.suffix in (".csproj", ".dll")
    )
    for flag in ["--version", "-v", "version"]:
        try:
            if is_dotnet:
                project = bin_path
                if project.is_dir():
                    csproj = list(project.glob("*.csproj"))
                    if csproj:
                        project = csproj[0]
                cmd = [
                    "dotnet", "run", "--no-build", "-c", "Release",
                    "--project", str(project), "--", flag,
                ]
            else:
                cmd = [str(bin_path), flag]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = [
                    l.strip()
                    for l in result.stdout.strip().splitlines()
                    if l.strip()
                ]
                return lines[-1] if lines else None
        except Exception:
            continue
    return None


def get_consumer(client: str, bin_path: Path) -> Any:
    """Detect and create consumer, passing extra config like state-bin."""
    config = load_config()
    client_config = config.get(client, {})
    extra_kwargs: Dict[str, Any] = {}

    # Pass state-bin if configured (e.g. reth uses revm for state)
    state_bin_str = client_config.get("state-bin", "")
    if state_bin_str:
        extra_kwargs["state_binary"] = Path(state_bin_str).expanduser().resolve()

    try:
        return FixtureConsumerTool.from_binary_path(
            binary_path=bin_path, trace=False, **extra_kwargs
        )
    except Exception:
        from execution_testing.client_clis.clis.nethermind import (
            NethtestFixtureConsumer,
        )
        return NethtestFixtureConsumer.from_binary_path(
            binary_path=bin_path, trace=False
        )


def get_bin_path(client: str, test_type: str | None = None) -> Path:
    """Resolve binary path for a client from config, skip if not configured.

    Supports per-type binary overrides (e.g. state-bin for reth/revm).
    """
    config = load_config()
    client_config = config.get(client, {})
    # Check for type-specific binary first
    bin_str = ""
    if test_type:
        bin_str = client_config.get(f"{test_type}-bin", "")
    if not bin_str:
        bin_str = client_config.get("bin", "")
    if not bin_str:
        pytest.skip(f"{client}: not configured in {CONFIG_FILE}")
    bin_path = Path(bin_str).expanduser().resolve()
    assert bin_path.exists(), f"binary not found: {bin_str}"
    return bin_path


def run_version(client: str) -> None:
    """Check binary exists and version is detectable."""
    bin_path = get_bin_path(client)
    version = detect_version(bin_path)
    if version is None:
        import warnings
        warnings.warn(
            f"{client}: could not detect version from {bin_path}"
        )


def run_health(client: str, test_type: str) -> None:
    """Run a sanity fixture for a client + test type."""
    # Always detect consumer from main binary, not type-specific override
    main_bin = get_bin_path(client)
    consumer = get_consumer(client, main_bin)
    # Verify type-specific binary exists if configured
    type_bin = get_bin_path(client, test_type)
    _ = type_bin  # just check it exists (get_bin_path asserts)

    fixture_format = FORMAT_MAP[test_type]
    assert fixture_format in consumer.fixture_formats, (
        f"{client}: {test_type} not supported"
    )

    subdir = TYPE_TO_SUBDIR[test_type]
    fixture_file = next((SANITY_DIR / subdir).glob("*.json"), None)
    assert fixture_file is not None, f"sanity fixture missing for {test_type}"

    data = json.loads(fixture_file.read_text())
    first_name = next(iter(data.keys()))

    consumer.consume_fixture(
        fixture_format=fixture_format,
        fixture_path=fixture_file,
        fixture_name=first_name,
    )


# --- geth ---


def test_geth_version() -> None:
    """Geth version detection."""
    run_version("geth")


def test_geth_state() -> None:
    """Geth state test sanity check."""
    run_health("geth", "state")


def test_geth_block() -> None:
    """Geth block test sanity check."""
    run_health("geth", "block")


def test_geth_engine() -> None:
    """Geth engine test sanity check."""
    run_health("geth", "engine")


# --- besu ---


def test_besu_version() -> None:
    """Besu version detection."""
    run_version("besu")


def test_besu_state() -> None:
    """Besu state test sanity check."""
    run_health("besu", "state")


def test_besu_block() -> None:
    """Besu block test sanity check."""
    run_health("besu", "block")


def test_besu_engine() -> None:
    """Besu engine test sanity check."""
    run_health("besu", "engine")


# --- nethermind ---


def test_nethermind_version() -> None:
    """Nethermind version detection."""
    run_version("nethermind")


def test_nethermind_state() -> None:
    """Nethermind state test sanity check."""
    run_health("nethermind", "state")


def test_nethermind_block() -> None:
    """Nethermind block test sanity check."""
    run_health("nethermind", "block")


def test_nethermind_engine() -> None:
    """Nethermind engine test sanity check."""
    run_health("nethermind", "engine")


# --- erigon ---


def test_erigon_version() -> None:
    """Erigon version detection."""
    run_version("erigon")


def test_erigon_state() -> None:
    """Erigon state test sanity check."""
    run_health("erigon", "state")


def test_erigon_block() -> None:
    """Erigon block test sanity check."""
    run_health("erigon", "block")


def test_erigon_engine() -> None:
    """Erigon engine test sanity check."""
    run_health("erigon", "engine")


# --- reth ---


def test_reth_version() -> None:
    """Reth version detection."""
    run_version("reth")


def test_reth_state() -> None:
    """Reth state test sanity check."""
    run_health("reth", "state")


def test_reth_block() -> None:
    """Reth block test sanity check."""
    run_health("reth", "block")


def test_reth_engine() -> None:
    """Reth engine test sanity check."""
    run_health("reth", "engine")


# --- ethrex ---


def test_ethrex_version() -> None:
    """Ethrex version detection."""
    run_version("ethrex")


def test_ethrex_state() -> None:
    """Ethrex state test sanity check."""
    run_health("ethrex", "state")


def test_ethrex_block() -> None:
    """Ethrex block test sanity check."""
    run_health("ethrex", "block")


def test_ethrex_engine() -> None:
    """Ethrex engine test sanity check."""
    run_health("ethrex", "engine")


# --- nimbus ---


def test_nimbus_version() -> None:
    """Nimbus version detection."""
    run_version("nimbus")


def test_nimbus_state() -> None:
    """Nimbus state test sanity check."""
    run_health("nimbus", "state")
