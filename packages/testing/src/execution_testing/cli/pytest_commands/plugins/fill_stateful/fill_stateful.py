"""
Pytest plugin for stateful fixture filling via ``testing_buildBlockV1``.

Produces ``BlockchainEngineStatefulFixture`` JSON files by executing
tests against a live network.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, List, Sequence

import pytest

from execution_testing.base_types import Bytes, Hash, HexNumber, Number
from execution_testing.test_types import EOA
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
from execution_testing.rpc import TestingRPC
from execution_testing.rpc.rpc_types import (
    GetPayloadResponse,
    PayloadAttributes,
    TransactionProtocol,
)
from execution_testing.test_types.phase_manager import TestPhase

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

        Checks two sources on each transaction, in order:

        1. ``test_phase`` — set at creation time by
           ``TestPhaseManager`` context managers.
        2. ``metadata.phase`` — set explicitly by the pre-alloc
           and execute plugins (e.g. ``"setup"`` for funding).

        Returns ``None`` when transactions are unavailable, carry
        no phase, or contain mixed phases.
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
    params: List[Any] = [response.execution_payload]

    if response.blobs_bundle is not None:
        params.append(response.blobs_bundle.blob_versioned_hashes())
    if captured.payload_attributes.parent_beacon_block_root is not None:
        params.append(captured.payload_attributes.parent_beacon_block_root)
    if response.execution_requests is not None:
        params.append(response.execution_requests)

    return FixtureEngineNewPayload(
        params=tuple(params),
        new_payload_version=captured.new_payload_version,
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
    """Add stateful-fill-specific options."""
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
        type=str,
        help="Private key of a funded account on the target network.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Configure the stateful fill plugin."""
    config.option.use_testing_build_block = True
    config.option.skip_cleanup = True
    config.engine_rpc_supported = True  # type: ignore[attr-defined]
    config.skip_transition_forks = True  # type: ignore[attr-defined]
    config.single_fork_mode = True  # type: ignore[attr-defined]

    if is_help_or_collectonly_mode(config):
        return

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
    snapshot_block: dict,  # noqa: ARG001 — force snapshot first
    recording_rpc: RecordingTestingRPC | None,  # noqa: ARG001 — force recorder first
    session_fork: Any,
    session_worker_key: EOA,
    eth_rpc: Any,
    sender_funding_transactions_gas_price: int,
    session_temp_folder: Path,
) -> None:
    """Deploy required contracts AFTER snapshot_block is captured.

    Overrides pre_alloc's version to guarantee ordering: the raw
    snapshot is recorded before any blocks are built.
    """
    from filelock import FileLock

    from execution_testing.cli.pytest_commands.plugins.execute.contracts import (
        check_deterministic_factory_deployment,
        deploy_deterministic_factory_contract,
    )

    base_lock_file = session_temp_folder / "execute_required_contracts.lock"
    with FileLock(base_lock_file):
        if (
            check_deterministic_factory_deployment(
                eth_rpc=eth_rpc, fork=session_fork
            )
            is None
        ):
            deploy_deterministic_factory_contract(
                eth_rpc=eth_rpc,
                seed_key=session_worker_key,
                gas_price=sender_funding_transactions_gas_price,
                tx_index=0,
            )


@pytest.fixture(scope="session")
def session_temp_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Provide a session-scoped temp folder (replaces concurrency plugin)."""
    return tmp_path_factory.mktemp("fill_stateful")


@pytest.fixture(scope="session")
def worker_count() -> int:
    """Always single-worker for stateful filling."""
    return 1


@pytest.fixture(scope="session")
def seed_key(eth_rpc: Any, request: pytest.FixtureRequest) -> EOA:
    """Load the seed key from --rpc-seed-key (replaces remote_seed_sender)."""
    key_str = request.config.getoption("rpc_seed_key")
    assert key_str, "--rpc-seed-key is required for fill-stateful"
    eoa = EOA(key=int(key_str, 16), nonce=0)
    account = eth_rpc.get_account(eoa, skip_code=True)
    eoa.nonce = Number(account.nonce)
    return eoa


@pytest.fixture(scope="session")
def session_worker_key(seed_key: EOA) -> EOA:
    """Use the seed key directly as the worker key (replaces sender)."""
    return seed_key


@pytest.fixture(scope="function")
def worker_key(eth_rpc: Any, session_worker_key: EOA) -> EOA:
    """Sync the worker key nonce before each test (replaces sender)."""
    account = eth_rpc.get_account(session_worker_key, skip_code=True)
    session_worker_key.nonce = Number(account.nonce)
    return session_worker_key


@pytest.fixture(scope="session")
def sender_funding_transactions_gas_price(eth_rpc: Any) -> int:
    """Gas price for funding transactions (replaces sender)."""
    return eth_rpc.gas_price()


@pytest.fixture(scope="session")
def sender_fund_refund_gas_limit() -> int:
    """Gas limit for fund/refund transactions (replaces sender)."""
    return 21_000


@pytest.fixture(scope="session")
def snapshot_block(eth_rpc: Any) -> dict:
    """Capture the client's current head as the snapshot reference.

    With ``execute_required_contracts`` overridden as a no-op, this
    captures the raw datadir head — the true snapshot that
    benchmarkoor will load.
    """
    block = eth_rpc.get_block_by_number("latest")
    assert block is not None, "Could not fetch snapshot block"
    logger.info(
        f"Snapshot block {block['number']} "
        f"hash={block['hash'][:20]}..."
    )
    return block


@pytest.fixture(scope="session")
def recording_rpc(
    eth_rpc: Any,
    session_fork: Fork | TransitionFork,
) -> RecordingTestingRPC | None:
    """Wrap the ``testing_rpc`` with a recording layer."""
    inner = getattr(eth_rpc, "testing_rpc", None)
    if inner is None:
        return None
    recorder = RecordingTestingRPC(inner, session_fork)
    eth_rpc.testing_rpc = recorder
    return recorder


@pytest.fixture(scope="session")
def start_block(
    eth_rpc: Any,
    execute_required_contracts: None,  # noqa: ARG001
) -> dict:
    """Capture the head after global setup (factory deploy etc.).

    Each test's ``setupEngineNewPayloads`` chain from this block.
    ``debug_setHead`` rewinds to this block between tests.
    """
    block = eth_rpc.get_block_by_number("latest")
    assert block is not None, "Could not fetch start block"
    logger.info(
        f"Start block {block['number']} "
        f"hash={block['hash'][:20]}..."
    )
    return block


_pre_run_written = False


def _maybe_write_pre_run(
    recording_rpc: RecordingTestingRPC,
    snapshot_block: dict,
    start_block: dict,
    session_fork: Fork | TransitionFork,
    config: Any,
) -> None:
    """Write global setup blocks to ``pre_run/global_setup.json`` once."""
    global _pre_run_written  # noqa: PLW0603
    if _pre_run_written:
        return
    _pre_run_written = True

    snapshot_num = int(HexNumber(snapshot_block["number"]))
    start_num = int(HexNumber(start_block["number"]))
    pre_run_captured = [
        c for c in recording_rpc.captured
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
    eth_rpc: Any,
) -> Generator[None, None, None]:
    """Clear recorder before test, package fixture after.

    On the first test, saves global setup blocks (between snapshot
    and start) to ``pre_run/global_setup.json``.  After each test,
    resets the chain to ``start_block`` via ``debug_setHead``.
    """
    if recording_rpc is None:
        yield
        return

    # On first test, write global setup blocks as pre-run fixture.
    _maybe_write_pre_run(
        recording_rpc, snapshot_block, start_block,
        session_fork, request.config,
    )

    recording_rpc.clear()
    yield

    if not recording_rpc.captured:
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

    info = _node_to_test_info(request.node)
    fixture_collector.add_fixture(info, fixture)
    logger.info(f"Captured stateful fixture for {request.node.nodeid}")

    # Reset chain to start block so the next test begins from
    # identical post-global-setup state.
    start_hex = start_block["number"]
    logger.info(f"Resetting chain to start block {start_hex}")
    import requests as http_requests  # noqa: PLC0415

    http_requests.post(
        eth_rpc.url,
        json={
            "jsonrpc": "2.0",
            "method": "debug_setHead",
            "params": [start_hex],
            "id": 1,
        },
    ).raise_for_status()


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,  # noqa: ARG001
) -> None:
    """Merge partial fixture files after all tests complete."""
    if is_help_or_collectonly_mode(session.config):
        return

    output_dir = Path(session.config.getoption("output"))
    merge_partial_fixture_files(output_dir)
    logger.info(f"Fixtures written to {output_dir}")
