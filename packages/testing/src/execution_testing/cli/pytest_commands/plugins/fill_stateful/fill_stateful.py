"""
Fill-native stateful fixture filling plugin.

Drives block construction via ``testing_buildBlockV1`` against a live EL
client, using fill's standard spec loop (``BlockchainTest.generate`` →
``make_stateful_fixture``). Emits ``BlockchainEngineStatefulFixture`` JSON.

Overrides fill's ``t8n`` / ``session_t8n`` fixtures to inject a
``ClientBackend``. Reuses execute's ``Alloc`` (via
``execute.pre_alloc`` plugin) so test authors keep calling
``pre.fund_eoa`` / ``pre.deploy_contract``; those enqueue setup
transactions that ``make_stateful_fixture`` materialises as a
setup-phase block prepended to ``self.blocks``.
"""

import os
import secrets
from pathlib import Path
from typing import Any, Generator, List
from urllib.parse import urlparse, urlunparse

import pytest
from filelock import FileLock

from execution_testing.base_types import (
    Address,
    Hash,
    HexNumber,
    Number,
)
from execution_testing.client_clis import ClientBackend
from execution_testing.client_clis.cli_types import EnginePayloadMetadata
from execution_testing.fixtures import FixtureFillingPhase
from execution_testing.fixtures.blockchain import (
    StatefulPreRunFixture,
)
from execution_testing.forks import (
    Fork,
    ForkSetAdapter,
    InvalidForkError,
    TransitionFork,
)
from execution_testing.logging import get_logger
from execution_testing.rpc import DebugRPC, EngineRPC, EthRPC
from execution_testing.specs.blockchain import (
    payload_metadata_to_fixture,
)
from execution_testing.test_types import EOA
from execution_testing.test_types.chain_config_types import (
    ChainConfigDefaults,
)

from ..execute import contracts
from ..execute.rpc.chain_builder_eth_rpc import ChainBuilderEthRPC
from ..execute.rpc.hive import (
    build_client_files,
    build_client_genesis_dict,
    build_genesis_header,
    build_hive_environment,
)
from ..shared.helpers import is_help_or_collectonly_mode
from ..shared.live_client_flags import FEE_BUMP_MULTIPLIER

# 1 billion ETH. Withdrawals are Gwei (u64-capped); much higher risks
# overflow on some clients, this is plenty for any single fill session.
SEED_FUNDING_WEI = 10**9 * 10**18

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# CLI options + config
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Add fill-stateful-specific command-line options.

    Live-client flags (``--default-gas-price``, ``--get-payload-wait-time``,
    ``--max-tx-per-batch``, ``--transaction-gas-limit``, ...) live in
    :mod:`plugins.shared.live_client_flags`, loaded by our ini.
    """
    group = parser.getgroup(
        "fill_stateful", "Arguments for stateful fixture filling"
    )
    group.addoption(
        "--hive-mode",
        action="store_true",
        dest="hive_mode",
        default=False,
        help=(
            "Fill stateful tests using Hive as a backend, skipping the "
            "requirement for Kurtosis or snapshot clients. Used mainly for "
            "debugging tests in stateful mode."
        ),
    )
    group.addoption(
        "--hive-simulator",
        action="store",
        dest="hive_simulator",
        default=os.environ.get("HIVE_SIMULATOR"),
        help=(
            "The Hive simulator endpoint, e.g. http://127.0.0.1:3000. By "
            "default, the value is taken from the HIVE_SIMULATOR environment "
            "variable."
        ),
    )
    group.addoption(
        "--rpc-seed-key",
        action="store",
        dest="rpc_seed_key",
        default=None,
        type=str,
        help=(
            "Private key for signing transactions. Optional — a random "
            "key is generated and funded via CL withdrawal if omitted."
        ),
    )
    group.addoption(
        "--snapshot-block",
        action="store",
        dest="snapshot_block",
        default=None,
        type=str,
        help=(
            "Anchor the snapshot to a specific block. Accepts a 0x-prefixed "
            "32-byte block hash (recommended — survives a chain reorg on "
            "the live client) or a block number (hex or decimal). When "
            "omitted, the client's ``latest`` block is used and recorded "
            "by hash. The produced fixtures are anchored by hash regardless."
        ),
    )


def _resolve_session_fork(
    config: pytest.Config,
) -> Fork | TransitionFork:
    """
    Resolve the single fork from ``--fork`` in hive mode.

    Runs in ``pytest_configure`` before forks.py populates
    ``selected_fork_set``, so we can't use ``session_fork`` here — the
    hive genesis/ruleset must be built before remote.py's pytest_configure
    pings the (not-yet-started) client.
    """
    fork_arg = config.getoption("single_fork", default="")
    if not fork_arg:
        pytest.exit(
            "--fork is required in --hive-mode (single-fork only).",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    try:
        fork_set = ForkSetAdapter.validate_python(fork_arg)
    except InvalidForkError:
        pytest.exit(
            f"Unsupported fork provided to --fork: {fork_arg!r}",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    if len(fork_set) != 1:
        pytest.exit(
            f"Expected exactly one fork in --hive-mode, got {len(fork_set)} "
            f"({sorted(f.name() for f in fork_set)}).",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    return next(iter(fork_set))


def _hive_chain_id(config: pytest.Config) -> int:
    """Resolve chain id from CLI/env, defaulting to ChainConfigDefaults."""
    cli_value = config.getoption("chain_id", default=None)
    if cli_value is not None:
        return int(cli_value)
    env_value = os.environ.get("CHAIN_ID")
    if env_value is not None:
        return int(env_value)
    return ChainConfigDefaults.chain_id


def _configure_hive(config: pytest.Config) -> None:
    """
    Start a hive simulator session and a single execution client, then
    rewrite ``config.option`` so the rest of the plugin stack (remote.py
    in particular) connects to the hive-managed client.
    """
    hive_simulator_url = config.getoption("hive_simulator")
    if hive_simulator_url is None:
        pytest.exit(
            "The HIVE_SIMULATOR environment variable is not set.\n\n"
            "If running locally, start hive in --dev mode, for example:\n"
            "./hive --dev --client go-ethereum\n\n"
            "and set the HIVE_SIMULATOR to the reported URL. For example, "
            "in bash:\n"
            "export HIVE_SIMULATOR=http://127.0.0.1:3000\n"
            "or in fish:\n"
            "set -x HIVE_SIMULATOR http://127.0.0.1:3000"
        )
    from hive.simulation import Simulation

    session_fork = _resolve_session_fork(config)
    chain_id = _hive_chain_id(config)

    simulator = Simulation(url=hive_simulator_url)
    suite = simulator.start_suite(
        name="fill-stateful test suite",
        description="Test suite used to drive a fill-stateful session",
    )
    config.hive_test_suite = suite  # type: ignore[attr-defined]
    base_test = suite.start_test(
        name="fill-stateful base test",
        description=(
            "Base test in the fill-stateful suite hosting the long-lived "
            "execution client."
        ),
    )
    config.hive_base_test = base_test  # type: ignore[attr-defined]

    # base_pre=None: seed key funded via CL withdrawal and deterministic
    # factory deployed on-chain by ``_session_pre_run``, so genesis only
    # needs the fork's required system contracts.
    pre_alloc, genesis_header = build_genesis_header(session_fork, None)
    genesis_dict = build_client_genesis_dict(pre_alloc, genesis_header)

    client_type = simulator.client_types()[0]
    client = base_test.start_client(
        client_type=client_type,
        environment=build_hive_environment(session_fork, chain_id),
        files=build_client_files(genesis_dict),
    )
    if client is None:
        pytest.exit(
            f"Unable to start hive client {client_type.name}. Check the "
            "hive server logs for more information."
        )
    config.hive_client = client  # type: ignore[attr-defined]
    logger.info(
        f"Started hive client {client_type.name} at {client.ip} "
        f"(fork={session_fork.name()}, chain_id={chain_id})"
    )

    config.option.rpc_endpoint = f"http://{client.ip}:8545"
    config.option.engine_endpoint = f"http://{client.ip}:8551"
    if (
        config.getoption("engine_jwt_secret", default=None) is None
        and config.getoption("engine_jwt_secret_file", default=None) is None
    ):
        config.option.engine_jwt_secret = EngineRPC.DEFAULT_JWT_SECRET
    if config.getoption("chain_id", default=None) is None:
        config.option.chain_id = chain_id


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """
    Configure the fill-stateful session.

    Filler handles output-dir/--clean/FixtureCollector; we only set
    fill-stateful flags and auto-derive endpoints + chain id.
    """
    config.option.use_testing_build_block = True
    config.option.skip_cleanup = True
    config.engine_rpc_supported = True  # type: ignore[attr-defined]
    config.skip_transition_forks = True  # type: ignore[attr-defined]
    config.single_fork_mode = True  # type: ignore[attr-defined]
    # Fail loudly on stub_parametrize with no matching --address-stubs
    # instead of pytest's default silent skip on empty parametrize.
    config.require_stub_match = True  # type: ignore[attr-defined]
    config.addinivalue_line(
        "markers",
        "missing_stubs(message): fill-stateful policy marker; "
        "pytest_runtest_call fails the test with ``message``.",
    )
    config.filling_phase = FixtureFillingPhase.FILL_STATEFUL  # type: ignore[attr-defined]

    # Help/collect-only never talks to a client; skip endpoint defaulting.
    if is_help_or_collectonly_mode(config):
        return

    config.hive_test_suite = None  # type: ignore[attr-defined]
    config.hive_base_test = None  # type: ignore[attr-defined]
    config.hive_client = None  # type: ignore[attr-defined]
    if config.getoption("hive_mode", default=False):
        _configure_hive(config)
    else:
        if not config.getoption("rpc_endpoint", default=None):
            config.option.rpc_endpoint = "http://localhost:8545"
        if not config.getoption("engine_endpoint", default=None):
            parsed = urlparse(config.getoption("rpc_endpoint"))
            config.option.engine_endpoint = urlunparse(
                parsed._replace(netloc=f"{parsed.hostname}:8551")
            )

        if not config.getoption("chain_id", default=None):
            rpc = EthRPC(config.getoption("rpc_endpoint"))
            config.option.chain_id = rpc.chain_id()
            logger.info(f"Auto-detected chain ID: {config.option.chain_id}")


def pytest_unconfigure(config: pytest.Config) -> None:
    """Tear down hive resources started in ``pytest_configure``."""
    client = getattr(config, "hive_client", None)
    if client is not None:
        try:
            client.stop()
        except Exception as e:
            logger.warning(f"Failed to stop hive client: {e}")
        config.hive_client = None  # type: ignore[attr-defined]

    base_test = getattr(config, "hive_base_test", None)
    if base_test is not None:
        from hive.testing import HiveTestResult

        test_pass = (
            getattr(config, "_fill_stateful_session_failed", False) is False
        )
        try:
            base_test.end(
                result=HiveTestResult(
                    test_pass=test_pass,
                    details=(
                        "fill-stateful session complete"
                        if test_pass
                        else "fill-stateful session had failures"
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to end hive base test: {e}")
        config.hive_base_test = None  # type: ignore[attr-defined]

    suite = getattr(config, "hive_test_suite", None)
    if suite is not None:
        try:
            suite.end()
        except Exception as e:
            logger.warning(f"Failed to end hive test suite: {e}")
        config.hive_test_suite = None  # type: ignore[attr-defined]


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Record overall session pass/fail for the hive teardown report."""
    del exitstatus
    if session.testsfailed > 0:
        session.config._fill_stateful_session_failed = True  # type: ignore[attr-defined]


def pytest_runtest_call(item: pytest.Item) -> None:
    """Fail in the call phase (→ FAILED, not ERROR) on ``missing_stubs``."""
    for marker in item.iter_markers("missing_stubs"):
        pytest.fail(marker.args[0], pytrace=False)


# ---------------------------------------------------------------------------
# Support fixtures (replacements for execute's sender/concurrency plugins)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def session_temp_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Session temp folder (replaces concurrency plugin)."""
    return tmp_path_factory.mktemp("fill_stateful")


@pytest.fixture(scope="session")
def worker_count() -> int:
    """Single-worker filling."""
    return 1


@pytest.fixture(scope="session")
def seed_key(eth_rpc: EthRPC, request: pytest.FixtureRequest) -> EOA:
    """Load or generate the seed key used for all session funding."""
    key_str = request.config.getoption("rpc_seed_key")
    if key_str:
        try:
            eoa = EOA(key=key_str, nonce=0)
        except Exception:
            pytest.fail(
                f"--rpc-seed-key must be a 32-byte hex string, "
                f"got: {key_str!r}"
            )
        account = eth_rpc.get_account(eoa, skip_code=True)
        eoa.nonce = Number(account.nonce)
    else:
        eoa = EOA(key=int.from_bytes(secrets.token_bytes(32)), nonce=0)
        logger.info("Generated random seed key (funded via withdrawal)")
    return eoa


@pytest.fixture(scope="session")
def session_worker_key(seed_key: EOA) -> EOA:
    """Alias of ``seed_key`` under the name pre_alloc's ``Alloc`` expects."""
    return seed_key


@pytest.fixture(scope="function")
def worker_key(eth_rpc: EthRPC, session_worker_key: EOA) -> EOA:
    """Sync seed key nonce before each test."""
    account = eth_rpc.get_account(session_worker_key, skip_code=True)
    session_worker_key.nonce = Number(account.nonce)
    return session_worker_key


@pytest.fixture(scope="session")
def sender_funding_transactions_gas_price(eth_rpc: EthRPC) -> int:
    """Pinned gas price for session-level funding transactions."""
    return eth_rpc.gas_price()


@pytest.fixture(scope="session")
def sender_fund_refund_gas_limit(
    session_fork: Fork | TransitionFork,
) -> int:
    """Intrinsic gas for the funding tx, derived from the fork."""
    fork = session_fork.fork_at(block_number=0, timestamp=0)
    return fork.transaction_intrinsic_cost_calculator()()


@pytest.fixture()
def max_gas_limit_per_test(
    request: pytest.FixtureRequest,
    session_fork: Fork | TransitionFork,
) -> int | None:
    """
    Override of ``live_client_flags.max_gas_limit_per_test`` — fall back
    to ``Fork.transaction_gas_limit_cap()`` (EIP-7825) when the CLI flag
    is unset. Returns ``None`` on pre-Osaka forks (no cap).
    """
    cli_value = request.config.getoption("max_gas_per_test")
    if cli_value is not None:
        return cli_value
    fork_at_genesis = session_fork.fork_at(block_number=0, timestamp=0)
    return fork_at_genesis.transaction_gas_limit_cap()


# Other live-client fixtures (``max_transactions_per_batch``,
# ``default_*``, fee fields, ``dry_run``, ...) come from
# ``shared.live_client_flags``. ``skip_cleanup`` from ``execute.pre_alloc``;
# we force it on in ``pytest_configure``.


# ---------------------------------------------------------------------------
# Backend + session setup
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def debug_rpc(eth_rpc: EthRPC) -> DebugRPC:
    """DebugRPC on the same endpoint as eth_rpc (for debug_setHead)."""
    return DebugRPC(eth_rpc.url)


@pytest.fixture(scope="session")
def client_backend(
    eth_rpc: ChainBuilderEthRPC,
    session_fork: Fork | TransitionFork,
    default_gas_price: int | None,
    default_max_fee_per_gas: int | None,
    default_max_priority_fee_per_gas: int | None,
    default_max_fee_per_blob_gas: int | None,
) -> ClientBackend:
    """
    Create the ClientBackend; snapshot/start block populated later.

    Session fees are pinned here (CLI defaults, else a one-shot live
    query bumped 1.5x) so ``make_stateful_fixture`` can size pre-alloc
    funding without mutating ``TransactionDefaults``.
    """
    assert eth_rpc.testing_rpc is not None, (
        "fill-stateful requires a client exposing the `testing` namespace"
    )
    # Share TestingRPC with ChainBuilderEthRPC so both code paths drive
    # the same client.
    backend = ClientBackend(
        testing_rpc=eth_rpc.testing_rpc,
        engine_rpc=eth_rpc.engine_rpc,
        eth_rpc=eth_rpc,
        fork=session_fork,
    )

    priority_fee = default_max_priority_fee_per_gas
    if priority_fee is None:
        priority_fee = int(
            eth_rpc.max_priority_fee_per_gas() * FEE_BUMP_MULTIPLIER
        )
    max_fee = default_max_fee_per_gas
    if max_fee is None:
        max_fee = int(eth_rpc.gas_price() * FEE_BUMP_MULTIPLIER)
    if priority_fee > max_fee:
        max_fee = priority_fee + 1
    blob_fee = default_max_fee_per_blob_gas
    if blob_fee is None:
        blob_fee = int(eth_rpc.blob_base_fee() * FEE_BUMP_MULTIPLIER)
    gas_price = (
        default_gas_price
        if default_gas_price is not None
        else max_fee + priority_fee
    )

    backend.gas_price = gas_price
    backend.max_fee_per_gas = max_fee
    backend.max_priority_fee_per_gas = priority_fee
    backend.max_fee_per_blob_gas = blob_fee
    logger.info(
        "ClientBackend fees pinned: "
        f"gas_price={gas_price / 10**9:.2f} Gwei, "
        f"max_fee={max_fee / 10**9:.2f} Gwei, "
        f"priority={priority_fee / 10**9:.2f} Gwei, "
        f"blob={blob_fee / 10**9:.2f} Gwei"
    )
    return backend


@pytest.fixture(scope="session")
def snapshot_block(
    request: pytest.FixtureRequest, eth_rpc: "ChainBuilderEthRPC"
) -> Any:
    """
    Resolve the snapshot anchor to a client block dict.

    Accepts a 32-byte hash (preferred — survives reorgs), an integer
    block number (hex/dec), or ``None`` for ``latest``. The returned
    block's ``hash`` is what we record as the fixture anchor.
    """
    snapshot_arg = request.config.getoption("snapshot_block", default=None)
    if not snapshot_arg:
        block = eth_rpc.get_block_by_number("latest")
        if block is None:
            pytest.exit("Failed to fetch 'latest' block as snapshot anchor")
        return block

    stripped = snapshot_arg.strip()
    block_hash: Hash | None = None
    try:
        block_hash = Hash(stripped)
    except Exception:
        pass
    if block_hash:
        block = eth_rpc.get_block_by_hash(block_hash)
        if block is None:
            pytest.exit(
                f"--snapshot-block hash {stripped} not found on client"
            )
        return block

    try:
        number = int(stripped, 0)
    except ValueError:
        pytest.exit(
            f"--snapshot-block must be a 0x-prefixed 32-byte hash or an "
            f"integer block number; got {snapshot_arg!r}"
        )
    block = eth_rpc.get_block_by_number(number)
    if block is None:
        pytest.exit(f"--snapshot-block number {number} not found on client")
    return block


@pytest.fixture(scope="session", autouse=True)
def _session_pre_run(
    client_backend: ClientBackend,
    eth_rpc: ChainBuilderEthRPC,
    session_worker_key: EOA,
    session_fork: Fork | TransitionFork,
    snapshot_block: Any,
    sender_funding_transactions_gas_price: int,
    session_temp_folder: Path,
    request: pytest.FixtureRequest,
) -> None:
    """
    Session pre-run: capture snapshot, fund seed, deploy factory, capture
    start block, write ``pre_run/<start_block_hash>.json``.

    The file is named after the start block hash so per-test
    ``BlockchainEngineStatefulFixture`` instances reference their setup
    file implicitly via their own ``start_block_hash`` field — leaves
    room for multiple pre-run files (e.g. different setup variants off
    one snapshot) without coordinating filenames.

    Pre-run helpers return their built ``EnginePayloadMetadata`` directly;
    we collect them into ``captured`` and serialise via
    ``payload_metadata_to_fixture``.
    """
    if is_help_or_collectonly_mode(request.config):
        return

    # 1. Snapshot anchor. Either way, the client-returned hash is what we
    #    record — a later reorg can't silently re-anchor by block number.
    client_backend.snapshot_block = snapshot_block
    logger.info(
        f"Snapshot block {snapshot_block['number']} "
        f"hash={snapshot_block['hash'][:20]}..."
    )

    # 2. Fund seed key via CL withdrawal; helper returns the built payload.
    captured: List[EnginePayloadMetadata] = []
    fund_payload = eth_rpc.fund_via_withdrawals(
        [(Address(session_worker_key), SEED_FUNDING_WEI)]
    )
    if fund_payload is not None:
        captured.append(fund_payload)
    logger.info(f"Funded {Address(session_worker_key)} via withdrawal")

    # 3. Deploy deterministic factory if not already present.
    lock_file = session_temp_folder / "fill_stateful_setup.lock"
    with FileLock(lock_file):
        if (
            contracts.check_deterministic_factory_deployment(
                eth_rpc=eth_rpc, fork=session_fork
            )
            is None
        ):
            _, deploy_payloads = (
                contracts.deploy_deterministic_factory_contract(
                    eth_rpc=eth_rpc,
                    seed_key=session_worker_key,
                    gas_price=sender_funding_transactions_gas_price,
                    tx_index=0,
                )
            )
            captured.extend(deploy_payloads)

    # 4. Capture start block (head after global setup).
    start_block = eth_rpc.get_block_by_number("latest")
    assert start_block is not None, "Failed to fetch start block"
    client_backend.start_block = start_block
    logger.info(
        f"Start block {start_block['number']} "
        f"hash={start_block['hash'][:20]}..."
    )

    # 5. Persist captured payloads to pre_run/<start_block_hash>.json.
    #    Per-test fixtures already carry start_block_hash; naming the
    #    pre-run file after that hash makes lookup a direct path build.
    if captured:
        output_dir = Path(request.config.getoption("output"))
        pre_run_dir = (
            output_dir / "blockchain_tests_stateful_engine" / "pre_run"
        )
        pre_run_dir.mkdir(parents=True, exist_ok=True)
        fork_at_genesis = session_fork.fork_at(block_number=0, timestamp=0)
        payloads = [payload_metadata_to_fixture(p) for p in captured]
        start_block_hash = Hash(start_block["hash"])
        fixture = StatefulPreRunFixture(
            network=str(fork_at_genesis),
            snapshot_block_number=HexNumber(snapshot_block["number"]),
            snapshot_block_hash=Hash(snapshot_block["hash"]),
            start_block_number=HexNumber(start_block["number"]),
            start_block_hash=start_block_hash,
            payloads=payloads,
        )
        pre_run_file = pre_run_dir / f"{start_block_hash}.json"
        pre_run_file.write_text(
            fixture.model_dump_json(by_alias=True, indent=2, exclude_none=True)
        )
        logger.info(
            f"Wrote {len(payloads)} pre-run payloads to {pre_run_file}"
        )


# ---------------------------------------------------------------------------
# Override fill's t8n/session_t8n with ClientBackend (last-loaded wins).
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True, scope="session")
def session_t8n(
    client_backend: ClientBackend,
    _session_pre_run: None,
) -> Generator[ClientBackend, None, None]:
    """
    Override fill's session_t8n; ``_session_pre_run`` is a dependency-only
    handle forcing snapshot/start capture before fill's spec loop runs.
    """
    del _session_pre_run
    yield client_backend
    client_backend.shutdown()


@pytest.fixture(autouse=True, scope="function")
def t8n(
    session_t8n: ClientBackend,
) -> Generator[ClientBackend, None, None]:
    """Override: no per-test reset needed for ClientBackend."""
    yield session_t8n


# ---------------------------------------------------------------------------
# Per-test lifecycle
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True, scope="function")
def _reset_chain_between_tests(
    client_backend: ClientBackend,
    debug_rpc: DebugRPC,
    eth_rpc: "ChainBuilderEthRPC",
) -> Generator[None, None, None]:
    """
    Rewind to start_block after each test so the chain is identical for
    every fill. ``debug_setHead`` only takes a number, so after the
    rewind we re-fetch ``latest`` and fail loudly if the hash drifted
    (e.g. live reorg of a same-numbered block).
    """
    yield
    if client_backend.start_block is None:
        return
    start_hex = client_backend.start_block["number"]
    expected_hash = client_backend.start_block["hash"]
    # Skip when head already at start (geth rejects same-block setHead).
    current_head = eth_rpc.get_block_by_number("latest")
    if current_head is not None and current_head["hash"] == expected_hash:
        return
    try:
        debug_rpc.set_head(start_hex)
    except Exception as e:
        pytest.exit(f"debug_setHead failed — subsequent fixtures invalid: {e}")
    head = eth_rpc.get_block_by_number("latest")
    if head is None or head["hash"] != expected_hash:
        observed = head["hash"] if head is not None else "<none>"
        pytest.exit(
            f"debug_setHead landed on hash {observed} but expected "
            f"{expected_hash} (start_block at number {start_hex}). The "
            "live chain may have reorged out from under fill-stateful; "
            "rerun against a quiescent client or use --snapshot-block "
            "with an explicit hash."
        )
