"""Health check for consume direct client binaries."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

from execution_testing.client_clis.fixture_consumer_tool import (
    FixtureConsumerTool,
)

# Bundled sanity fixtures (one per test type, smallest available)
SANITY_DIR = (
    Path(__file__).parent
    / "plugins/consume/direct/sanity_fixtures"
)

# Known clients with default binary names and supported test types
CLIENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "geth": {
        "default_bin": "evm",
        "types": ["state", "block", "engine"],
    },
    "besu": {
        "default_bin": "evmtool",
        "types": ["state", "block", "engine"],
    },
    "nethermind": {
        "default_bin": "nethtest",
        "types": ["state", "block", "engine"],
    },
    "erigon": {
        "default_bin": "evm",
        "types": ["state", "block", "engine"],
    },
    "reth": {
        "default_bin": "ef-test-runner",
        "types": ["state", "block", "engine"],
    },
    "ethrex": {
        "default_bin": "ef_tests",
        "types": ["state", "block", "engine"],
    },
    "nimbus": {
        "default_bin": "evmstate",
        "types": ["state"],
    },
}

CONFIG_FILE = "consume-direct.toml"

TEMPLATE = """\
# Consume direct client binary configuration.
# Set the path to each client's EVM test binary.
# Run `consume direct health` to verify.
#
# Use state-bin to override the binary for state tests only (e.g. reth uses revm).

# [geth]
# bin = "~/ethereum/clients/go-ethereum/build/bin/evm"

# [besu]
# bin = "~/ethereum/clients/besu/ethereum/evmtool/build/install/evmtool/bin/evmtool"

# [nethermind]
# bin = "~/ethereum/clients/nethermind/src/Nethermind/Nethermind.Test.Runner"

# [erigon]
# bin = "~/ethereum/clients/erigon/build/bin/evm"

# [reth]
# bin = "~/ethereum/clients/reth/target/release/ef-test-runner"
# state-bin = "~/ethereum/clients/revm/target/release/revme"

# [ethrex]
# bin = "~/ethereum/clients/ethrex/target/release/ef_tests"

# [nimbus]
# bin = "~/ethereum/clients/nimbus-eth1/build/evmstate"
"""


def load_config(config_path: Path) -> Dict[str, Dict[str, str]]:
    """Load the consume-direct.toml config file."""
    if not config_path.exists():
        return {}
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def create_template(config_path: Path) -> None:
    """Create a template config file."""
    config_path.write_text(TEMPLATE)


def detect_version(bin_path: Path) -> Optional[str]:
    """Try to get version string from a binary."""
    for flag in ["--version", "-v", "version"]:
        try:
            result = subprocess.run(
                [str(bin_path), flag],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = [
                    line.strip()
                    for line in result.stdout.strip().splitlines()
                    if line.strip()
                ]
                return lines[-1] if lines else None
        except Exception:
            continue
    return None


_TYPE_TO_SUBDIR = {
    "state": "state_tests",
    "block": "blockchain_tests",
    "engine": "blockchain_tests_engine",
}


def run_sanity_test(
    bin_path: Path,
    test_type: str,
) -> tuple[bool, str]:
    """Run a bundled sanity fixture and return (passed, message)."""
    subdir = _TYPE_TO_SUBDIR[test_type]
    fixture_dir = SANITY_DIR / subdir
    fixture_file = next(fixture_dir.glob("*.json"), None)
    if fixture_file is None:
        return False, "sanity fixture missing"
    if not fixture_file.exists():
        return False, "sanity fixture missing"

    try:
        consumer = FixtureConsumerTool.from_binary_path(
            binary_path=bin_path, trace=False
        )
    except Exception:
        try:
            from execution_testing.client_clis.clis.nethermind import (
                NethtestFixtureConsumer,
            )
            consumer = NethtestFixtureConsumer.from_binary_path(
                binary_path=bin_path, trace=False
            )
        except Exception as e:
            return False, f"detection failed: {e}"

    from execution_testing.fixtures import (
        BlockchainEngineFixture,
        BlockchainFixture,
        StateFixture,
    )
    format_map = {
        "state": StateFixture,
        "block": BlockchainFixture,
        "engine": BlockchainEngineFixture,
    }
    fixture_format = format_map[test_type]

    if fixture_format not in consumer.fixture_formats:
        return False, "not supported"

    data = json.loads(fixture_file.read_text())
    first_name = next(iter(data.keys()))

    try:
        consumer.consume_fixture(
            fixture_format=fixture_format,
            fixture_path=fixture_file,
            fixture_name=first_name,
        )
        return True, "ok"
    except Exception as e:
        return False, str(e)[:80]


def run_health_check(
    config_path: Path,
    client_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
) -> int:
    """Run health checks and print results. Returns exit code."""
    config = load_config(config_path)

    if not config:
        print(f"\nNo {CONFIG_FILE} found. Creating template...")
        create_template(config_path)
        print(f"Created {config_path}")
        print(
            "Edit it to add your client binary paths, "
            "then re-run.\n"
        )
        return 1

    clients = list(CLIENT_REGISTRY.keys())
    if client_filter:
        clients = [c for c in clients if c == client_filter]
        if not clients:
            print(f"Unknown client: {client_filter}")
            print(
                f"Available: {', '.join(CLIENT_REGISTRY.keys())}"
            )
            return 1

    print()
    print(
        f"  {'Client':<14} {'Version':<30} "
        f"state  block  engine"
    )
    print(
        f"  {'------':<14} {'-------':<30} "
        f"-----  -----  ------"
    )

    total_checks = 0
    passed_checks = 0
    configured = 0

    for client in clients:
        info = CLIENT_REGISTRY[client]
        client_config = config.get(client, {})
        bin_str = client_config.get("bin", "")

        if not bin_str:
            print(
                f"  {client:<14} {'-':<30} "
                f"-      -      -      (not configured)"
            )
            continue

        configured += 1
        bin_path = Path(bin_str).expanduser().resolve()

        if not bin_path.exists():
            print(
                f"  {client:<14} {'-':<30} "
                f"x      x      x      (not found)"
            )
            continue

        version = detect_version(bin_path) or "unknown"
        if len(version) > 28:
            version = version[:28] + ".."

        results: List[str] = []
        for test_type in ["state", "block", "engine"]:
            if test_type not in info["types"]:
                results.append("-  ")
                continue
            if type_filter and test_type != type_filter:
                results.append(".  ")
                continue

            total_checks += 1
            passed, msg = run_sanity_test(bin_path, test_type)
            if passed:
                passed_checks += 1
                results.append("ok ")
            else:
                results.append("FAIL")

        status_cols = "    ".join(results)
        print(f"  {client:<14} {version:<30} {status_cols}")

    print()
    print(
        f"  {configured}/{len(clients)} clients configured, "
        f"{passed_checks}/{total_checks} checks passed"
    )
    print()

    return 0 if passed_checks == total_checks else 1
