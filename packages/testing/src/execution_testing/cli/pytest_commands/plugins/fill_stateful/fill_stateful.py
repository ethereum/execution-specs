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

import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, List, Sequence
from urllib.parse import urlparse, urlunparse

import pytest
from filelock import FileLock

from execution_testing.base_types import (
    Address,
    Bytes,
    Hash,
    HexNumber,
    Number,
)
from execution_testing.client_clis import ClientBackend
from execution_testing.fixtures.blockchain import (
    BlockchainEngineStatefulFixture,
    FixtureEngineNewPayload,
    StatefulPreRunFixture,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.logging import get_logger
from execution_testing.rpc import DebugRPC, EthRPC, TestingRPC
from execution_testing.rpc.rpc_types import (
    GetPayloadResponse,
    PayloadAttributes,
    TransactionProtocol,
)
from execution_testing.specs.benchmark import BenchmarkTest
from execution_testing.specs.blockchain import BlockchainTest
from execution_testing.test_types import EOA
from execution_testing.test_types.transaction_types import TransactionDefaults

from ..execute import contracts
from ..execute.rpc.chain_builder_eth_rpc import ChainBuilderEthRPC
from ..shared.helpers import is_help_or_collectonly_mode

logger = get_logger(__name__)


# Restrict every BaseTest spec that fill-stateful cares about to emit
# ONLY the stateful engine fixture. Fill's filler plugin reads
# ``supported_fixture_formats`` during ``pytest_generate_tests`` (at
# collection time); mutating at module load is the earliest hook that
# fires before pytest reads the list.
#
# BlockchainTest is the generic class; BenchmarkTest is its subclass
# used by all tests under ``tests/benchmark/``. Both override the
# ClassVar so both need patching.
BlockchainTest.supported_fixture_formats = [
    BlockchainEngineStatefulFixture
]
BenchmarkTest.supported_fixture_formats = [
    BlockchainEngineStatefulFixture
]


# ---------------------------------------------------------------------------
# Session setup recorder — minimal MITM scoped ONLY to global pre-run blocks
# (factory deploy + seed funding). Per-test block building does NOT go
# through this wrapper; it goes directly through ClientBackend.evaluate.
# ---------------------------------------------------------------------------


@dataclass
class _CapturedSetup:
    """A block captured during global pre-run setup."""

    payload_attributes: PayloadAttributes
    response: GetPayloadResponse
    new_payload_version: int
    forkchoice_updated_version: int


class _SessionSetupRecorder:
    """
    Wraps ``TestingRPC`` during session pre-run to capture blocks emitted by
    factory deploy + withdrawal funding. The captured payloads are written
    to ``pre_run/global_setup.json``.

    Unwrapped after session setup; per-test fills use the raw ``TestingRPC``
    via ``ClientBackend`` directly.
    """

    def __init__(
        self,
        inner: TestingRPC,
        fork: Fork | TransitionFork,
    ) -> None:
        """Initialize wrapping the inner RPC."""
        self._inner = inner
        self._fork = fork
        self.captured: List[_CapturedSetup] = []

    def build_block(
        self,
        parent_block_hash: Hash,
        payload_attributes: PayloadAttributes,
        transactions: Sequence[TransactionProtocol] | None,
        extra_data: Bytes | None = None,
        *,
        version: int = 1,
    ) -> GetPayloadResponse:
        """Delegate to the inner RPC and record the response."""
        response = self._inner.build_block(
            parent_block_hash=parent_block_hash,
            payload_attributes=payload_attributes,
            transactions=transactions,
            extra_data=extra_data,
            version=version,
        )
        block_fork = self._fork.fork_at(
            block_number=response.execution_payload.number,
            timestamp=response.execution_payload.timestamp,
        )
        np_version = block_fork.engine_new_payload_version()
        fcu_version = block_fork.engine_forkchoice_updated_version()
        assert np_version is not None
        assert fcu_version is not None
        self.captured.append(
            _CapturedSetup(
                payload_attributes=payload_attributes,
                response=response,
                new_payload_version=np_version,
                forkchoice_updated_version=fcu_version,
            )
        )
        return response

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the wrapped RPC."""
        return getattr(self._inner, name)


def _captured_to_payload(
    captured: _CapturedSetup,
) -> FixtureEngineNewPayload:
    """Materialise a captured setup response into a FixtureEngineNewPayload."""
    version = captured.new_payload_version
    response = captured.response
    params: List[Any] = [response.execution_payload]
    if version >= 3:
        blob_hashes = (
            response.blobs_bundle.blob_versioned_hashes()
            if response.blobs_bundle is not None
            else []
        )
        params.append(blob_hashes)
        params.append(captured.payload_attributes.parent_beacon_block_root)
    if version >= 4 and response.execution_requests is not None:
        params.append(response.execution_requests)
    return FixtureEngineNewPayload(
        params=tuple(params),
        new_payload_version=version,
        forkchoice_updated_version=captured.forkchoice_updated_version,
    )


# ---------------------------------------------------------------------------
# CLI options + config
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Add fill-stateful-specific command-line options.

    Also registers a minimal subset of ``execute.execute``'s options that
    downstream fixtures from ``execute.pre_alloc`` / ``execute.rpc.remote``
    still read. We avoid loading the full ``execute.execute`` plugin
    because its ``pytest_addoption`` (``--no-html`` etc.) and its
    ``pytest_generate_tests`` both conflict with filler's.
    """
    group = parser.getgroup(
        "fill_stateful", "Arguments for stateful fixture filling"
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
    # Options that downstream execute/* fixtures require but which live in
    # execute.execute (a plugin we deliberately do not load — see above).
    group.addoption(
        "--get-payload-wait-time",
        action="store",
        dest="get_payload_wait_time",
        type=float,
        default=0.3,
        help=(
            "Seconds to wait between engine_forkchoiceUpdated and "
            "engine_getPayload."
        ),
    )
    group.addoption(
        "--max-tx-per-batch",
        action="store",
        dest="max_tx_per_batch",
        type=int,
        default=None,
        help="Max transactions per JSON-RPC batch (None = unlimited).",
    )
    group.addoption(
        "--transaction-gas-limit",
        action="store",
        dest="transaction_gas_limit",
        type=int,
        default=None,
        help="Max gas per setup transaction (None = env default).",
    )
    group.addoption(
        "--max-gas-per-test",
        action="store",
        dest="max_gas_per_test",
        type=int,
        default=None,
        help="Max gas limit across a test's transactions (None = unlimited).",
    )
    group.addoption(
        "--transactions-per-block",
        action="store",
        dest="transactions_per_block",
        type=int,
        default=None,
        help="Transactions per block before producing the next (None = all).",
    )
    group.addoption(
        "--default-max-fee-per-blob-gas",
        action="store",
        dest="default_max_fee_per_blob_gas",
        type=int,
        default=None,
        help="Default blob gas max fee (None = 2× current).",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """
    Configure the fill-stateful session.

    Filler's own ``pytest_configure`` handles output-dir, --clean, and the
    ``FixtureCollector``; we only set fill-stateful-specific flags and
    auto-derive endpoints/chain id from the client.
    """
    config.option.use_testing_build_block = True
    config.option.skip_cleanup = True
    config.engine_rpc_supported = True  # type: ignore[attr-defined]
    config.skip_transition_forks = True  # type: ignore[attr-defined]
    config.single_fork_mode = True  # type: ignore[attr-defined]

    if not config.getoption("rpc_endpoint", default=None):
        config.option.rpc_endpoint = "http://localhost:8545"
    if not config.getoption("engine_endpoint", default=None):
        parsed = urlparse(config.getoption("rpc_endpoint"))
        config.option.engine_endpoint = urlunparse(
            parsed._replace(netloc=f"{parsed.hostname}:8551")
        )

    if is_help_or_collectonly_mode(config):
        return

    if not config.getoption("chain_id", default=None):
        rpc = EthRPC(config.getoption("rpc_endpoint"))
        config.option.chain_id = rpc.chain_id()
        logger.info(f"Auto-detected chain ID: {config.option.chain_id}")

    # Scale TransactionDefaults to match the live client's fee market so
    # queued pre-alloc setup txs (which fall back to these defaults) are
    # accepted. The t8n-oriented defaults (10 wei) are not usable against
    # a live chain with any base-fee history.
    live_gas_price = EthRPC(config.getoption("rpc_endpoint")).gas_price()
    TransactionDefaults.gas_price = max(live_gas_price * 2, 10**10)
    TransactionDefaults.max_fee_per_gas = TransactionDefaults.gas_price
    TransactionDefaults.max_priority_fee_per_gas = 10**9
    logger.info(
        f"Set TransactionDefaults: gas_price="
        f"{TransactionDefaults.gas_price} wei "
        f"(~{TransactionDefaults.gas_price / 10**9:.2f} gwei)"
    )


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
        clean = key_str.removeprefix("0x").removeprefix("0X")
        if len(clean) != 64 or not all(
            c in "0123456789abcdefABCDEF" for c in clean
        ):
            pytest.fail(
                f"--rpc-seed-key must be a 32-byte hex string, "
                f"got: {key_str!r}"
            )
        eoa = EOA(key=int(clean, 16), nonce=0)
        account = eth_rpc.get_account(eoa, skip_code=True)
        eoa.nonce = Number(account.nonce)
    else:
        eoa = EOA(key=int.from_bytes(secrets.token_bytes(32)), nonce=0)
        logger.info("Generated random seed key (funded via withdrawal)")
    return eoa


@pytest.fixture(scope="session")
def session_worker_key(seed_key: EOA) -> EOA:
    """execute.pre_alloc expects this fixture name; alias seed_key."""
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
def sender_fund_refund_gas_limit() -> int:
    """Gas limit for session-level funding transactions."""
    return 21_000


@pytest.fixture(scope="session")
def max_transactions_per_batch() -> int | None:
    """
    Cap for JSON-RPC transaction batch size (replaces execute.execute).

    Fill-stateful is single-worker; no batching cap is needed.
    """
    return None


@pytest.fixture(scope="session")
def use_testing_build_block() -> bool:
    """Always build blocks via testing_buildBlockV1 in fill-stateful mode."""
    return True


@pytest.fixture(scope="session")
def skip_cleanup() -> bool:
    """Skip per-test cleanup — debug_setHead handles state reset."""
    return True


@pytest.fixture(scope="session")
def dry_run() -> bool:
    """Fill-stateful always executes against the live client."""
    return False


@pytest.fixture(scope="session")
def max_fee_per_gas(eth_rpc: EthRPC) -> int:
    """Default max_fee_per_gas derived from the connected client."""
    return eth_rpc.gas_price() * 2


@pytest.fixture(scope="session")
def max_priority_fee_per_gas() -> int:
    """Modest priority fee for fill-stateful setup transactions."""
    return 10**9


@pytest.fixture(scope="session")
def default_max_fee_per_gas(max_fee_per_gas: int) -> int:
    """Alias — execute.execute exposes this name."""
    return max_fee_per_gas


@pytest.fixture(scope="session")
def default_max_priority_fee_per_gas(max_priority_fee_per_gas: int) -> int:
    """Alias — execute.execute exposes this name."""
    return max_priority_fee_per_gas


@pytest.fixture(scope="session")
def default_gas_price(max_fee_per_gas: int) -> int:
    """Gas price alias for legacy tx helpers."""
    return max_fee_per_gas


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
) -> ClientBackend:
    """Create the ClientBackend; snapshot/start block populated later."""
    assert eth_rpc.testing_rpc is not None, (
        "fill-stateful requires a client exposing the `testing` namespace"
    )
    # eth_rpc.testing_rpc is the shared TestingRPC used by ChainBuilderEthRPC
    # for pre-alloc sends. ClientBackend uses the same instance so any
    # recorder installed downstream observes both code paths.
    backend = ClientBackend(
        testing_rpc=eth_rpc.testing_rpc,
        engine_rpc=eth_rpc.engine_rpc,
        eth_rpc=eth_rpc,
        fork=session_fork,
    )
    return backend


@pytest.fixture(scope="session", autouse=True)
def _session_pre_run(
    client_backend: ClientBackend,
    eth_rpc: ChainBuilderEthRPC,
    session_worker_key: EOA,
    session_fork: Fork | TransitionFork,
    sender_funding_transactions_gas_price: int,
    session_temp_folder: Path,
    request: pytest.FixtureRequest,
) -> None:
    """
    Session pre-run: capture snapshot, fund seed, deploy factory, capture
    start block, write ``pre_run/global_setup.json``.

    Scoped MITM: the TestingRPC is temporarily wrapped in a recorder for
    the duration of pre-run. Per-test fills bypass the recorder entirely
    via ``ClientBackend.evaluate``.
    """
    if is_help_or_collectonly_mode(request.config):
        return

    # 1. Snapshot block (raw datadir head)
    snapshot_block = eth_rpc.get_block_by_number("latest")
    assert snapshot_block is not None, "Failed to fetch snapshot block"
    client_backend.snapshot_block = snapshot_block
    logger.info(
        f"Snapshot block {snapshot_block['number']} "
        f"hash={snapshot_block['hash'][:20]}..."
    )

    # 2. Install session-setup recorder on the shared TestingRPC.
    raw_testing_rpc = client_backend.testing_rpc
    recorder = _SessionSetupRecorder(raw_testing_rpc, session_fork)
    client_backend.testing_rpc = recorder  # type: ignore[assignment]
    eth_rpc.testing_rpc = recorder  # type: ignore[assignment]

    try:
        # 3. Fund seed key via CL withdrawal.
        funding_wei = 10**9 * 10**18
        eth_rpc.fund_via_withdrawals(
            [(Address(session_worker_key), funding_wei)]
        )
        logger.info(
            f"Funded {Address(session_worker_key)} via withdrawal"
        )

        # 4. Deploy deterministic factory if not already present.
        lock_file = session_temp_folder / "fill_stateful_setup.lock"
        with FileLock(lock_file):
            if (
                contracts.check_deterministic_factory_deployment(
                    eth_rpc=eth_rpc, fork=session_fork
                )
                is None
            ):
                contracts.deploy_deterministic_factory_contract(
                    eth_rpc=eth_rpc,
                    seed_key=session_worker_key,
                    gas_price=sender_funding_transactions_gas_price,
                    tx_index=0,
                )
    finally:
        # 5. Uninstall the recorder.
        client_backend.testing_rpc = raw_testing_rpc
        eth_rpc.testing_rpc = raw_testing_rpc

    # 6. Capture start block (head after global setup).
    start_block = eth_rpc.get_block_by_number("latest")
    assert start_block is not None, "Failed to fetch start block"
    client_backend.start_block = start_block
    logger.info(
        f"Start block {start_block['number']} "
        f"hash={start_block['hash'][:20]}..."
    )

    # 7. Persist captured setup payloads to pre_run/global_setup.json.
    if recorder.captured:
        output_dir = Path(request.config.getoption("output"))
        pre_run_dir = (
            output_dir / "blockchain_tests_stateful_engine" / "pre_run"
        )
        pre_run_dir.mkdir(parents=True, exist_ok=True)
        fork_at_genesis = session_fork.fork_at(block_number=0, timestamp=0)
        payloads = [_captured_to_payload(c) for c in recorder.captured]
        fixture = StatefulPreRunFixture(
            network=str(fork_at_genesis),
            snapshot_block_number=HexNumber(snapshot_block["number"]),
            snapshot_block_hash=Hash(snapshot_block["hash"]),
            start_block_number=HexNumber(start_block["number"]),
            start_block_hash=Hash(start_block["hash"]),
            payloads=payloads,
        )
        (pre_run_dir / "global_setup.json").write_text(
            fixture.model_dump_json(
                by_alias=True, indent=2, exclude_none=True
            )
        )
        logger.info(
            f"Wrote {len(payloads)} pre-run payloads to "
            f"{pre_run_dir / 'global_setup.json'}"
        )


# ---------------------------------------------------------------------------
# Fill-plugin fixture overrides — replace t8n/session_t8n with ClientBackend.
# Fill's filler loads before this plugin, so these names override its
# versions via pytest's last-loaded-wins resolution.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True, scope="session")
def session_t8n(
    client_backend: ClientBackend,
    _session_pre_run: None,
) -> Generator[ClientBackend, None, None]:
    """Override: fill's session_t8n returns ClientBackend for stateful runs."""
    del _session_pre_run  # ordering only
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
) -> Generator[None, None, None]:
    """
    debug_setHead back to start_block after each test so every subsequent
    test fills against identical state.
    """
    yield
    if client_backend.start_block is None:
        return
    start_hex = client_backend.start_block["number"]
    try:
        debug_rpc.set_head(start_hex)
    except Exception as e:
        pytest.exit(
            f"debug_setHead failed — subsequent fixtures invalid: {e}"
        )
