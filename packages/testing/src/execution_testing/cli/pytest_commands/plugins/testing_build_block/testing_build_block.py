"""Pytest plugin wiring spamoor scenarios through ``testing_*`` RPCs."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import pytest

from execution_testing.base_types import Address, Hash
from execution_testing.forks import Fork, get_forks
from execution_testing.rpc import EngineRPC, EthRPC, TestingRPC
from execution_testing.test_types import EOA, Transaction

from .commit_block import commit_via_build, commit_via_commit

BLOAT_COMMIT_MODE_BUILD = "build"
BLOAT_COMMIT_MODE_COMMIT = "commit"
BLOAT_COMMIT_MODES = (BLOAT_COMMIT_MODE_BUILD, BLOAT_COMMIT_MODE_COMMIT)


@dataclass(frozen=True)
class BloatConfig:
    """Resolved CLI options for the testing-build-block plugin."""

    rpc_url: str
    engine_url: str
    jwt_secret: bytes
    signer_key: str
    chain_id: int
    block_version: int
    commit_mode: str


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ``--bloat-*`` CLI options for the plugin."""
    group = parser.getgroup(
        "testing_build_block",
        "Testing-namespace block commit options",
    )
    group.addoption(
        "--bloat-rpc-url",
        dest="bloat_rpc_url",
        default="http://localhost:8545",
        help="Execution client RPC URL (Eth+Testing modules).",
    )
    group.addoption(
        "--bloat-engine-url",
        dest="bloat_engine_url",
        default="http://localhost:8551",
        help="Execution client Engine API URL.",
    )
    group.addoption(
        "--bloat-jwt-secret-file",
        dest="bloat_jwt_secret_file",
        default=None,
        help="Path to a hex-encoded JWT secret file.",
    )
    group.addoption(
        "--bloat-signer-key",
        dest="bloat_signer_key",
        default=None,
        help="Hex private key of the funded sender.",
    )
    group.addoption(
        "--bloat-chain-id",
        dest="bloat_chain_id",
        type=int,
        default=1,
        help="Chain ID used when signing transactions.",
    )
    group.addoption(
        "--bloat-block-version",
        dest="bloat_block_version",
        type=int,
        default=1,
        help="``testing_buildBlockVX`` version to invoke.",
    )
    group.addoption(
        "--bloat-commit-mode",
        dest="bloat_commit_mode",
        choices=list(BLOAT_COMMIT_MODES),
        default=BLOAT_COMMIT_MODE_BUILD,
        help=(
            "``build`` drives newPayload+FCU; ``commit`` reserves the "
            "future single-shot endpoint."
        ),
    )
    group.addoption(
        "--bloat-fork",
        dest="bloat_fork",
        default=None,
        help="Override the active fork (defaults to latest known fork).",
    )
    group.addoption(
        "--bloat-config-file",
        dest="bloat_config_file",
        type=str,
        default="",
        help=(
            "Path to a spammer-export YAML. Parallels "
            "--spamoor-config-file; tx-shape overlay still happens in "
            "spamoor_config, this option only validates the YAML parses."
        ),
    )
    group.addoption(
        "--bloat-scenario-index",
        dest="bloat_scenario_index",
        type=int,
        default=0,
        help="0-indexed scenario entry to load from --bloat-config-file.",
    )
    group.addoption(
        "--bloat-strict",
        dest="bloat_strict",
        action="store_true",
        default=False,
        help=(
            "Fail the run when the selected YAML scenario uses keys the "
            "EST overlay does not support. Mirrors --spamoor-strict."
        ),
    )


def _load_jwt_secret(path: str | None) -> bytes:
    """
    Parse a hex-encoded JWT secret file, mirroring ``execute.remote``.

    Returns the raw secret bytes. Exits the pytest session with a
    descriptive message if the file is missing or malformed.
    """
    if path is None:
        pytest.exit(
            "--bloat-jwt-secret-file is required for the engine endpoint."
        )
    secret_path = Path(path)
    try:
        raw = secret_path.read_text().strip()
    except FileNotFoundError:
        pytest.exit(f"JWT secret file not found: {secret_path}")
    if raw.startswith("0x"):
        raw = raw[2:]
    try:
        return bytes.fromhex(raw)
    except ValueError:
        pytest.exit(
            "JWT secret file must contain a hex-encoded string; "
            f"got invalid content at {secret_path}"
        )


def _resolve_fork(name: str | None) -> Any:
    """Return the ``Fork`` matching *name* or the latest known fork."""
    forks = get_forks()
    if name is None:
        return forks[-1]
    lowered = name.lower()
    for fork in forks:
        if fork.name().lower() == lowered:
            return fork
    raise pytest.UsageError(
        f"Unknown --bloat-fork {name!r}; available: "
        f"{', '.join(f.name() for f in forks)}"
    )


@pytest.fixture(scope="session")
def bloat_config(request: pytest.FixtureRequest) -> BloatConfig:
    """Materialise CLI flags into an immutable ``BloatConfig``."""
    signer_key = request.config.getoption("bloat_signer_key")
    if signer_key is None:
        pytest.exit("--bloat-signer-key is required")
    bloat_config_file = request.config.getoption("bloat_config_file")
    if bloat_config_file:
        from ..spamoor.spamoor import (
            _load_scenario_from_yaml,
            _validate_yaml_keys,
        )

        entry = _load_scenario_from_yaml(
            bloat_config_file,
            int(request.config.getoption("bloat_scenario_index")),
        )
        strict = bool(request.config.getoption("bloat_strict"))
        if not strict:
            try:
                strict = bool(request.config.getoption("spamoor_strict"))
            except (ValueError, KeyError):
                pass
        _validate_yaml_keys(entry, strict=strict)
    jwt_secret = _load_jwt_secret(
        request.config.getoption("bloat_jwt_secret_file")
    )
    return BloatConfig(
        rpc_url=request.config.getoption("bloat_rpc_url"),
        engine_url=request.config.getoption("bloat_engine_url"),
        jwt_secret=jwt_secret,
        signer_key=signer_key,
        chain_id=int(request.config.getoption("bloat_chain_id")),
        block_version=int(request.config.getoption("bloat_block_version")),
        commit_mode=request.config.getoption("bloat_commit_mode"),
    )


@pytest.fixture(scope="session")
def bloat_testing_rpc(bloat_config: BloatConfig) -> TestingRPC:
    """Return the ``TestingRPC`` client bound to the bloat endpoint."""
    return TestingRPC(bloat_config.rpc_url)


@pytest.fixture(scope="session")
def bloat_engine_rpc(bloat_config: BloatConfig) -> EngineRPC:
    """Return the ``EngineRPC`` client authorised with the JWT secret."""
    return EngineRPC(
        bloat_config.engine_url,
        jwt_secret=bloat_config.jwt_secret,
    )


@pytest.fixture(scope="session")
def bloat_eth_rpc(bloat_config: BloatConfig) -> EthRPC:
    """Return the base ``EthRPC`` client for head/nonce queries."""
    return EthRPC(bloat_config.rpc_url)


@pytest.fixture(scope="session")
def bloat_fork(request: pytest.FixtureRequest) -> Fork:
    """Return the fork selected via ``--bloat-fork`` or latest."""
    return _resolve_fork(request.config.getoption("bloat_fork"))


@pytest.fixture(scope="session")
def bloat_signer(bloat_config: BloatConfig, bloat_eth_rpc: EthRPC) -> EOA:
    """Return an ``EOA`` seeded with the current on-chain nonce."""
    probe = EOA(key=bloat_config.signer_key, nonce=0)
    try:
        nonce = bloat_eth_rpc.get_transaction_count(probe, "latest")
    except Exception as exc:  # noqa: BLE001
        # Fail fast: a silent ``nonce=0`` fallback would collide with any
        # prior tx the signer has on chain and produce flaky "invalid
        # nonce" rejects that mask the real RPC error.
        raise pytest.UsageError(
            f"bloat_signer: failed to fetch on-chain nonce for "
            f"{probe} from {bloat_config.rpc_url}: {exc}"
        ) from exc
    # ``EOA.__new__`` short-circuits when ``address`` is already an
    # ``EOA``, so wrap it as a plain ``Address`` to force re-construction
    # with the freshly fetched nonce.
    return EOA(
        Address(probe),
        key=bloat_config.signer_key,
        nonce=nonce,
    )


@pytest.fixture
def bloat_commit_block(
    bloat_config: BloatConfig,
    bloat_testing_rpc: TestingRPC,
    bloat_engine_rpc: EngineRPC,
    bloat_eth_rpc: EthRPC,
    bloat_fork: Fork,
) -> Callable[[Sequence[Transaction]], Hash]:
    """Return a callable dispatching to the configured commit mode."""

    def _commit(txs: Sequence[Transaction]) -> Hash:
        if bloat_config.commit_mode == BLOAT_COMMIT_MODE_BUILD:
            return commit_via_build(
                testing_rpc=bloat_testing_rpc,
                engine_rpc=bloat_engine_rpc,
                eth_rpc=bloat_eth_rpc,
                fork=bloat_fork,
                txs=txs,
                version=bloat_config.block_version,
            )
        return commit_via_commit(
            testing_rpc=bloat_testing_rpc,
            eth_rpc=bloat_eth_rpc,
            fork=bloat_fork,
            txs=txs,
            version=bloat_config.block_version,
        )

    return _commit


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers for testing-build-block scenarios."""
    config.addinivalue_line(
        "markers",
        "testing_build_block: run testing-namespace block-commit tests",
    )
