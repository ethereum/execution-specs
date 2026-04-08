"""
Pytest plugin for stateful fixture filling via ``testing_buildBlockV1``.

Produces ``BlockchainEngineStatefulFixture`` JSON files by executing
tests against a live network.
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
from execution_testing.cli.pytest_commands.plugins.execute import (
    contracts,
)
from execution_testing.fixtures.blockchain import (
    BlockchainEngineStatefulFixture,
    FixtureConfig,
    FixtureEngineNewPayload,
    StatefulPreRunFixture,
)
from execution_testing.fixtures.collector import (
    FixtureCollector,
    TestInfo,
    merge_partial_fixture_files,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.logging import get_logger
from execution_testing.rpc import DebugRPC, EthRPC, TestingRPC
from execution_testing.rpc.rpc_types import (
    GetPayloadResponse,
    PayloadAttributes,
    TransactionProtocol,
)
from execution_testing.test_types import EOA
from execution_testing.test_types.phase_manager import TestPhase

from ..execute.rpc.chain_builder_eth_rpc import (
    ChainBuilderEthRPC,
)
from ..shared.helpers import is_help_or_collectonly_mode

logger = get_logger(__name__)


@dataclass
class CapturedPayload:
    """A recorded ``testing_buildBlockV1`` response with phase."""

    phase: TestPhase | None
    response: GetPayloadResponse
    payload_attributes: PayloadAttributes
    new_payload_version: int
    forkchoice_updated_version: int


class RecordingTestingRPC:
    """Wrap ``TestingRPC`` to record ``build_block`` responses."""

    def __init__(
        self,
        inner: TestingRPC,
        fork: Fork | TransitionFork,
    ) -> None:
        """Initialize with the inner RPC and fork."""
        self._inner = inner
        self._fork = fork
        self.captured: List[CapturedPayload] = []
        self.pre_run_written: bool = False  # set once, never reset

    def build_block(
        self,
        parent_block_hash: Hash,
        payload_attributes: PayloadAttributes,
        transactions: Sequence[TransactionProtocol] | None,
        extra_data: Bytes | None = None,
        *,
        version: int = 1,
    ) -> GetPayloadResponse:
        """Delegate to inner RPC and record the response."""
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
            CapturedPayload(
                phase=self._resolve_phase(transactions),
                response=response,
                payload_attributes=payload_attributes,
                new_payload_version=np_version,
                forkchoice_updated_version=fcu_version,
            )
        )
        return response

    @staticmethod
    def _resolve_phase(
        transactions: Sequence[TransactionProtocol] | None,
    ) -> TestPhase | None:
        """
        Derive the block phase from transaction metadata.

        Falls back from ``test_phase`` to ``metadata.phase``.
        If phases are mixed, SETUP takes precedence.
        """
        if not transactions:
            return None

        phases: set[TestPhase | None] = set()
        for tx in transactions:
            phase = getattr(tx, "test_phase", None)
            if phase is None:
                meta = getattr(tx, "metadata", None)
                if meta is not None:
                    phase = getattr(meta, "phase", None)
            phases.add(phase)

        phases.discard(None)
        if len(phases) == 1:
            return phases.pop()
        # Mixed phases: SETUP takes precedence (a block containing
        # any setup transaction is considered part of the setup).
        if TestPhase.SETUP in phases:
            return TestPhase.SETUP
        return None

    def clear(self) -> None:
        """Clear captured payloads between tests."""
        self.captured.clear()

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to inner RPC."""
        return getattr(self._inner, name)


def _to_fixture_payload(
    captured: CapturedPayload,
) -> FixtureEngineNewPayload:
    """Convert a captured payload to a ``FixtureEngineNewPayload``."""
    response = captured.response
    version = captured.new_payload_version
    # Positional params per engine_newPayloadVN:
    #   V1-V2: (executionPayload,)
    #   V3:    (executionPayload, blobVersionedHashes, beaconRoot)
    #   V4+:   (executionPayload, blobVersionedHashes, beaconRoot, requests)
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


def _node_to_test_info(node: pytest.Item) -> TestInfo:
    """Return test info from a pytest node."""
    return TestInfo(
        name=node.name,
        id=node.nodeid,
        original_name=node.originalname,  # type: ignore[attr-defined]
        module_path=Path(node.path),
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    fill_group = parser.getgroup(
        "fill_stateful",
        "Arguments for stateful fixture filling",
    )
    fill_group.addoption(
        "--output",
        action="store",
        dest="output",
        default="./fixtures",
        type=str,
        help="Output directory for generated fixtures.",
    )
    fill_group.addoption(
        "--rpc-seed-key",
        action="store",
        dest="rpc_seed_key",
        default=None,
        type=str,
        help="Private key for signing transactions. "
        "Optional — a random key is generated and funded via "
        "CL withdrawal if not provided.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Configure the stateful fill plugin."""
    config.option.use_testing_build_block = True
    config.option.skip_cleanup = True
    config.engine_rpc_supported = True  # type: ignore[attr-defined]
    config.skip_transition_forks = True  # type: ignore[attr-defined]
    config.single_fork_mode = True  # type: ignore[attr-defined]

    # Default RPC/Engine endpoints for local clients.
    if not config.getoption("rpc_endpoint", default=None):
        config.option.rpc_endpoint = "http://localhost:8545"
    if not config.getoption("engine_endpoint", default=None):
        parsed = urlparse(config.getoption("rpc_endpoint"))
        config.option.engine_endpoint = urlunparse(
            parsed._replace(netloc=f"{parsed.hostname}:8551")
        )

    if is_help_or_collectonly_mode(config):
        return

    # Auto-detect chain ID from the client if not provided.
    if not config.getoption("chain_id", default=None):
        rpc = EthRPC(config.getoption("rpc_endpoint"))
        config.option.chain_id = rpc.chain_id()
        logger.info(f"Auto-detected chain ID: {config.option.chain_id}")

    output_dir = Path(config.getoption("output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    config.fixture_collector = FixtureCollector(  # type: ignore[attr-defined]
        output_dir=output_dir,
        fill_static_tests=False,
        single_fixture_per_file=False,
        filler_path=Path(config.rootpath),
    )


@pytest.fixture(scope="session")
def fixture_collector(
    request: pytest.FixtureRequest,
) -> FixtureCollector:
    """Provide the FixtureCollector for streaming fixtures to disk."""
    return request.config.fixture_collector  # type: ignore[attr-defined]


# Replacements for dropped plugins (sender, concurrency, remote_seed_sender).


@pytest.fixture(scope="session", autouse=True)
def execute_required_contracts(
    snapshot_block: dict,
    recording_rpc: RecordingTestingRPC | None,
    session_fork: Fork | TransitionFork,
    session_worker_key: EOA,
    eth_rpc: ChainBuilderEthRPC,
    sender_funding_transactions_gas_price: int,
    session_temp_folder: Path,
) -> None:
    """
    Fund seed account via CL withdrawal and deploy required contracts.

    Ordering: snapshot_block → recording_rpc → this → start_block.
    Runs AFTER snapshot_block is captured so the raw datadir head
    is recorded first.  Funds the seed key via a withdrawal (works
    on any snapshot regardless of account balances), then deploys
    the deterministic factory.
    """
    del snapshot_block, recording_rpc  # used only for fixture ordering
    # Fund seed account via CL withdrawal.
    funding_wei = 10**9 * 10**18  # 1B ETH
    eth_rpc.fund_via_withdrawals([(Address(session_worker_key), funding_wei)])
    logger.info(f"Funded {Address(session_worker_key)} via withdrawal")

    # Deploy deterministic factory if not already present.
    base_lock_file = session_temp_folder / "execute_required_contracts.lock"
    with FileLock(base_lock_file):
        if (
            contracts.check_deterministic_factory_deployment(
                eth_rpc=eth_rpc, fork=session_fork
            )
            is None
        ):
            try:
                contracts.deploy_deterministic_factory_contract(
                    eth_rpc=eth_rpc,
                    seed_key=session_worker_key,
                    gas_price=sender_funding_transactions_gas_price,
                    tx_index=0,
                )
            except Exception as e:
                raise RuntimeError(
                    f"Error deploying deterministic factory: {e}"
                ) from e


@pytest.fixture(scope="session")
def session_temp_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Provide a session-scoped temp folder (replaces concurrency plugin)."""
    return tmp_path_factory.mktemp("fill_stateful")


@pytest.fixture(scope="session")
def worker_count() -> int:
    """Always single-worker for stateful filling."""
    return 1


@pytest.fixture(scope="session")
def seed_key(eth_rpc: EthRPC, request: pytest.FixtureRequest) -> EOA:
    """
    Load or generate a seed key for signing transactions.

    If ``--rpc-seed-key`` is provided, uses that key and syncs its
    nonce from the chain.  Otherwise generates a random one (funded
    via withdrawal in global setup).
    """
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
        key = int(clean, 16)
        eoa = EOA(key=key, nonce=0)
        account = eth_rpc.get_account(eoa, skip_code=True)
        eoa.nonce = Number(account.nonce)
    else:
        key = int.from_bytes(secrets.token_bytes(32))
        eoa = EOA(key=key, nonce=0)
        logger.info("Generated random seed key (funded via withdrawal)")
    return eoa


@pytest.fixture(scope="session")
def session_worker_key(seed_key: EOA) -> EOA:
    """Use the seed key directly as the worker key (replaces sender)."""
    return seed_key


@pytest.fixture(scope="function")
def worker_key(eth_rpc: EthRPC, session_worker_key: EOA) -> EOA:
    """Sync the worker key nonce before each test (replaces sender)."""
    account = eth_rpc.get_account(session_worker_key, skip_code=True)
    session_worker_key.nonce = Number(account.nonce)
    return session_worker_key


@pytest.fixture(scope="session")
def sender_funding_transactions_gas_price(eth_rpc: EthRPC) -> int:
    """Gas price for funding transactions (replaces sender)."""
    return eth_rpc.gas_price()


@pytest.fixture(scope="session")
def sender_fund_refund_gas_limit() -> int:
    """Gas limit for fund/refund transactions (replaces sender)."""
    return 21_000


@pytest.fixture(scope="session")
def snapshot_block(eth_rpc: EthRPC) -> dict:
    """
    Capture the raw datadir head before global setup.

    Resolved before ``execute_required_contracts`` via fixture
    dependency, so this records the pre-setup chain head.
    """
    block = eth_rpc.get_block_by_number("latest")
    assert block is not None, "Could not fetch snapshot block"
    logger.info(
        f"Snapshot block {block['number']} hash={block['hash'][:20]}..."
    )
    return block


@pytest.fixture(scope="session")
def debug_rpc(eth_rpc: EthRPC) -> DebugRPC:
    """Create a DebugRPC client from the same endpoint as eth_rpc."""
    return DebugRPC(eth_rpc.url)


@pytest.fixture(scope="session")
def recording_rpc(
    eth_rpc: ChainBuilderEthRPC,
    session_fork: Fork | TransitionFork,
) -> RecordingTestingRPC | None:
    """Wrap the ``testing_rpc`` with a recording layer."""
    if eth_rpc.testing_rpc is None:
        return None
    recorder = RecordingTestingRPC(eth_rpc.testing_rpc, session_fork)
    eth_rpc.testing_rpc = recorder  # type: ignore[assignment]
    return recorder


@pytest.fixture(scope="session")
def start_block(
    eth_rpc: EthRPC,
    execute_required_contracts: None,
) -> dict:
    """
    Capture the head after global setup (factory deploy etc.).

    Each test's ``setupEngineNewPayloads`` chain from this block.
    ``debug_setHead`` rewinds to this block between tests.
    """
    del execute_required_contracts  # used only for fixture ordering
    block = eth_rpc.get_block_by_number("latest")
    assert block is not None, "Could not fetch start block"
    logger.info(f"Start block {block['number']} hash={block['hash'][:20]}...")
    return block


def _maybe_write_pre_run(
    recording_rpc: RecordingTestingRPC,
    snapshot_block: dict,
    start_block: dict,
    session_fork: Fork | TransitionFork,
    config: Any,
) -> None:
    """Write global setup blocks to ``pre_run/global_setup.json`` once."""
    if recording_rpc.pre_run_written:
        return
    recording_rpc.pre_run_written = True

    snapshot_num = int(HexNumber(snapshot_block["number"]))
    start_num = int(HexNumber(start_block["number"]))
    pre_run_captured = [
        c
        for c in recording_rpc.captured
        if snapshot_num < c.response.execution_payload.number <= start_num
    ]
    payloads = [_to_fixture_payload(c) for c in pre_run_captured]
    if not payloads:
        return

    output_dir = Path(config.getoption("output"))
    pre_run_dir = output_dir / "blockchain_tests_stateful_engine" / "pre_run"
    pre_run_dir.mkdir(parents=True, exist_ok=True)

    fork = session_fork.fork_at(block_number=0, timestamp=0)
    fixture = StatefulPreRunFixture(
        network=str(fork),
        snapshot_block_number=HexNumber(snapshot_block["number"]),
        snapshot_block_hash=Hash(snapshot_block["hash"]),
        payloads=payloads,
    )

    pre_run_file = pre_run_dir / "global_setup.json"
    pre_run_file.write_text(
        fixture.model_dump_json(by_alias=True, indent=2, exclude_none=True)
    )
    logger.info(f"Wrote {len(payloads)} pre-run payloads to {pre_run_file}")


@pytest.fixture(autouse=True, scope="function")
def capture_stateful_fixture(
    request: pytest.FixtureRequest,
    recording_rpc: RecordingTestingRPC | None,
    snapshot_block: dict,
    start_block: dict,
    fixture_collector: FixtureCollector,
    session_fork: Fork | TransitionFork,
    debug_rpc: DebugRPC,
) -> Generator[None, None, None]:
    """
    Clear recorder before test, package fixture after.

    On the first test, saves global setup blocks (between snapshot
    and start) to ``pre_run/global_setup.json``.  After each test,
    resets the chain to ``start_block`` via ``debug_setHead``.
    """
    if recording_rpc is None:
        yield
        return

    # On first test, write global setup blocks as pre-run fixture.
    _maybe_write_pre_run(
        recording_rpc,
        snapshot_block,
        start_block,
        session_fork,
        request.config,
    )

    recording_rpc.clear()
    yield

    if not recording_rpc.captured:
        logger.warning(f"No payloads captured for {request.node.nodeid}")
        return

    setup_payloads = [
        _to_fixture_payload(c)
        for c in recording_rpc.captured
        if c.phase == TestPhase.SETUP
    ]
    execution_payloads = [
        _to_fixture_payload(c)
        for c in recording_rpc.captured
        if c.phase != TestPhase.SETUP
    ]

    last_captured = recording_rpc.captured[-1]
    last_block_hash = last_captured.response.execution_payload.block_hash

    fork = session_fork.fork_at(block_number=0, timestamp=0)
    fixture = BlockchainEngineStatefulFixture(
        fork=fork,
        last_block_hash=last_block_hash,
        config=FixtureConfig(fork=fork),
        snapshot_block_number=HexNumber(snapshot_block["number"]),
        snapshot_block_hash=Hash(snapshot_block["hash"]),
        start_block_number=HexNumber(start_block["number"]),
        start_block_hash=Hash(start_block["hash"]),
        setup_payloads=setup_payloads,
        payloads=execution_payloads,
    )

    # Populate _info metadata.
    fixture.info["comment"] = "`execution-specs` generated test"
    test_fn = getattr(request.node, "function", None)
    if test_fn and test_fn.__doc__:
        fixture.info["description"] = test_fn.__doc__.strip().split("\n")[0]

    info = _node_to_test_info(request.node)
    fixture_collector.add_fixture(info, fixture)
    logger.info(f"Captured stateful fixture for {request.node.nodeid}")

    # Reset chain to start block so the next test starts from
    # identical post-global-setup state.
    start_hex = start_block["number"]
    logger.info(f"Resetting chain to start block {start_hex}")
    try:
        debug_rpc.set_head(start_hex)
    except Exception as e:
        pytest.exit(
            f"debug_setHead failed — subsequent fixtures would be invalid: {e}"
        )


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
) -> None:
    """Merge partial fixture files after all tests complete."""
    del exitstatus
    if is_help_or_collectonly_mode(session.config):
        return

    collector = getattr(session.config, "fixture_collector", None)
    if collector is not None:
        collector.close_streaming_files()

    output_dir = Path(session.config.getoption("output"))
    merge_partial_fixture_files(output_dir)
    logger.info(f"Fixtures written to {output_dir}")
