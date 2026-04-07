"""
Pytest plugin for stateful fixture filling via ``testing_buildBlockV1``.

Produces ``BlockchainEngineStatefulFixture`` JSON files by executing
tests against a live network.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, List, Sequence

import pytest

from execution_testing.base_types import Bytes, Hash, HexNumber
from execution_testing.fixtures.blockchain import (
    BlockchainEngineStatefulFixture,
    FixtureConfig,
    FixtureEngineNewPayload,
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


@pytest.fixture(scope="session")
def snapshot_block(
    eth_rpc: Any,
    execute_required_contracts: None,  # noqa: ARG001
) -> dict:
    """
    Capture the client's current head as the snapshot reference.

    Depends on ``execute_required_contracts`` to ensure the
    deterministic factory is already deployed before we record
    the snapshot — otherwise the factory deployment block would
    sit between the snapshot and the first test payload.
    """
    block = eth_rpc.get_block_by_number("latest")
    assert block is not None, "Could not fetch snapshot block"
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


@pytest.fixture(autouse=True, scope="function")
def capture_stateful_fixture(
    request: pytest.FixtureRequest,
    recording_rpc: RecordingTestingRPC | None,
    snapshot_block: dict,
    fixture_collector: FixtureCollector,
    session_fork: Fork | TransitionFork,
    eth_rpc: Any,
) -> Generator[None, None, None]:
    """
    Clear recorder before test, package fixture after.

    After each test, resets the chain to the snapshot block via
    ``debug_setHead`` so the next test starts from identical state.
    """
    if recording_rpc is None:
        yield
        return

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
        setup_payloads=setup_payloads,
        payloads=execution_payloads,
    )

    info = _node_to_test_info(request.node)
    fixture_collector.add_fixture(info, fixture)
    logger.info(f"Captured stateful fixture for {request.node.nodeid}")

    # Reset chain to snapshot so the next test starts from identical
    # state.  This uses debug_setHead which rewinds the chain without
    # restarting the client process.
    snapshot_hex = snapshot_block["number"]
    logger.info(f"Resetting chain to snapshot block {snapshot_hex}")
    # Use a raw RPC call to avoid eth_ namespace prefixing.
    import requests as http_requests

    http_requests.post(
        eth_rpc.url,
        json={
            "jsonrpc": "2.0",
            "method": "debug_setHead",
            "params": [snapshot_hex],
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
