"""
Live execution client backend for ``BlockchainTest``.

``ClientBackend`` drives block construction via ``testing_buildBlockV1`` on a
running EL client instead of the classical t8n CLI/server path. It satisfies
the ``FillerBackend`` protocol so fill's spec loop
(``BlockchainTest.generate_block_data``) can dispatch to it transparently.

Used by ``fill --stateful`` to produce ``BlockchainEngineStatefulFixture`` JSON
from the same test definitions that the compute path fills via t8n — phase
info, block boundaries, and pre-alloc declarations flow unchanged.
"""

from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

from execution_testing.base_types import Bytes, Hash
from execution_testing.exceptions import ExceptionBase, ExceptionMapper
from execution_testing.forks import Fork, TransitionFork
from execution_testing.rpc import EngineRPC, EthRPC, TestingRPC
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    PayloadAttributes,
    PayloadStatusEnum,
)
from execution_testing.test_types import Requests, Transaction, Withdrawal
from execution_testing.test_types.block_access_list import BlockAccessList
from execution_testing.test_types.receipt_types import TransactionReceipt

from .cli_types import (
    LazyAllocJson,
    OpcodeCount,
    Result,
    Traces,
    TransitionToolOutput,
)
from .transition_tool import TransitionTool


class ClientBackendExceptionMapper(ExceptionMapper):
    """
    Exception mapper for live-client responses.

    ``reliable = False`` signals that engine API errors cannot be accurately
    mapped to EEST transaction/block exceptions; tests that assert on a
    specific failure mode should prefer the t8n path.
    """

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {}
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {}
    reliable: ClassVar[bool] = False


class ClientBackend:
    """
    ``FillerBackend`` driven by ``testing_buildBlockV1``.

    One instance wraps a live client connection. Subsequent ``evaluate`` calls
    advance the client's canonical chain via ``engine_newPayloadVX`` +
    ``engine_forkchoiceUpdatedVX`` so future blocks build on the previous one.
    """

    exception_mapper: ExceptionMapper
    snapshot_block: Dict[str, Any] | None
    """
    Raw datadir head (block dict from ``eth_getBlockByNumber``) captured
    before any session setup. Populated by the fill-stateful plugin at
    session start; read by ``make_stateful_fixture`` to emit
    ``snapshot_block_number`` / ``snapshot_block_hash``.
    """
    start_block: Dict[str, Any] | None
    """
    Client head after global pre-run setup (factory deploy, seed funding).
    Populated by the fill-stateful plugin after global setup; each test's
    block sequence chains off this.
    """

    # t8n-compatibility stubs — fill's filler plugin reads these on the
    # backend for book-keeping that has no analog for a live client.
    opcode_count: OpcodeCount | None = None
    output_cache: Any = None
    debug_dump_dir: Path | None = None
    call_counter: int = 0
    _info_metadata: Dict[str, Any]

    # Latest GetPayloadResponse from ``testing_buildBlockV1`` + the
    # version numbers to use for engine_newPayloadVX / FCU. Populated
    # each ``evaluate`` call; ``make_stateful_fixture`` reads it to
    # record the client's authoritative payload in the fixture instead
    # of the FixtureHeader-recomputed variant (which would disagree on
    # gas_limit etc. and produce a mismatched block hash).
    last_payload_response: Any = None
    last_new_payload_version: int = 0
    last_forkchoice_updated_version: int = 0
    last_parent_beacon_block_root: Hash | None = None

    def __init__(
        self,
        *,
        testing_rpc: TestingRPC,
        engine_rpc: EngineRPC,
        eth_rpc: EthRPC,
        fork: Fork | TransitionFork,
    ) -> None:
        """Initialize with the RPC clients and the session fork."""
        self.testing_rpc = testing_rpc
        self.engine_rpc = engine_rpc
        self.eth_rpc = eth_rpc
        self.fork = fork
        self.exception_mapper = ClientBackendExceptionMapper()
        self.snapshot_block = None
        self.start_block = None
        self._info_metadata = {}

    def version(self) -> str:
        """Return an identifier for this backend."""
        return f"ClientBackend[fork={self.fork}]"

    def shutdown(self) -> None:
        """No-op — owned by the fill-stateful plugin."""
        return

    def reset_traces(self) -> None:
        """No-op — traces not supported."""
        return

    def reset_opcode_count(self) -> None:
        """No-op — opcode counting not supported."""
        return

    def set_cache(self, *, key: str) -> bool:
        """No-op — caching not meaningful for a live client."""
        del key
        return False

    def remove_cache(self) -> None:
        """No-op — caching not meaningful for a live client."""
        return

    def increment_call_counter(self) -> int:
        """Increment and return the call counter (book-keeping only)."""
        previous = self.call_counter
        self.call_counter += 1
        return previous

    def get_next_transition_tool_output_path(
        self, call_id: int
    ) -> Optional[Path]:
        """Return ``None`` — debug dumps not supported."""
        del call_id
        return None

    def get_traces(self) -> List[Traces] | None:
        """Return ``None`` — traces are not available via the engine API."""
        return None

    def evaluate(
        self,
        *,
        transition_tool_data: TransitionTool.TransitionToolData,
        slow_request: bool = False,
    ) -> TransitionToolOutput:
        """Build a block via ``testing_buildBlockV1`` and return its result."""
        del slow_request  # not meaningful for the engine path
        env = transition_tool_data.env
        txs = transition_tool_data.txs
        block_fork = transition_tool_data.fork

        payload_attributes = self._payload_attributes(env, block_fork)
        parent_block_hash = Hash(env.parent_hash or 0)
        get_payload_response = self.testing_rpc.build_block(
            parent_block_hash=parent_block_hash,
            payload_attributes=payload_attributes,
            transactions=txs,
            extra_data=Bytes(env.extra_data),
        )
        self._finalize(
            get_payload_response,
            parent_beacon_block_root=(
                payload_attributes.parent_beacon_block_root
            ),
            block_fork=block_fork,
        )
        # Stash the client-authoritative payload for fill to pick up.
        self.last_payload_response = get_payload_response
        np_version = block_fork.engine_new_payload_version()
        fcu_version = block_fork.engine_forkchoice_updated_version()
        assert np_version is not None
        assert fcu_version is not None
        self.last_new_payload_version = np_version
        self.last_forkchoice_updated_version = fcu_version
        self.last_parent_beacon_block_root = (
            payload_attributes.parent_beacon_block_root
        )

        receipts = self._fetch_receipts(txs)
        result = self._build_result(
            built_payload=get_payload_response.execution_payload,
            execution_requests=get_payload_response.execution_requests,
            receipts=receipts,
            withdrawals=env.withdrawals,
            block_fork=block_fork,
        )
        alloc = LazyAllocJson(raw={}, _state_root=result.state_root)
        return TransitionToolOutput(alloc=alloc, result=result)

    def _payload_attributes(
        self,
        env: Any,
        block_fork: Fork,
    ) -> PayloadAttributes:
        """Build ``PayloadAttributes`` from the test's environment."""
        withdrawals = None
        if block_fork.header_withdrawals_required():
            withdrawals = list(env.withdrawals or [])
        parent_beacon_block_root = None
        if block_fork.header_beacon_root_required():
            parent_beacon_block_root = Hash(
                env.parent_beacon_block_root or 0
            )
        target_blobs_per_block = None
        max_blobs_per_block = None
        if block_fork.engine_payload_attribute_target_blobs_per_block():
            target_blobs_per_block = block_fork.target_blobs_per_block()
        if block_fork.engine_payload_attribute_max_blobs_per_block():
            max_blobs_per_block = block_fork.max_blobs_per_block()
        return PayloadAttributes(
            timestamp=int(env.timestamp),
            prev_randao=Hash(env.prev_randao or 0),
            suggested_fee_recipient=env.fee_recipient,
            withdrawals=withdrawals,
            parent_beacon_block_root=parent_beacon_block_root,
            target_blobs_per_block=target_blobs_per_block,
            max_blobs_per_block=max_blobs_per_block,
        )

    def _finalize(
        self,
        payload_response: Any,
        *,
        parent_beacon_block_root: Hash | None,
        block_fork: Fork,
    ) -> None:
        """Advance the chain with engine_newPayload + forkchoiceUpdated."""
        new_payload_version = block_fork.engine_new_payload_version()
        fcu_version = block_fork.engine_forkchoice_updated_version()
        assert new_payload_version is not None
        assert fcu_version is not None

        new_payload_args: List[Any] = [payload_response.execution_payload]
        if payload_response.blobs_bundle is not None:
            new_payload_args.append(
                payload_response.blobs_bundle.blob_versioned_hashes()
            )
        if parent_beacon_block_root is not None:
            new_payload_args.append(parent_beacon_block_root)
        if payload_response.execution_requests is not None:
            new_payload_args.append(payload_response.execution_requests)

        new_payload_response = self.engine_rpc.new_payload(
            *new_payload_args, version=new_payload_version
        )
        assert new_payload_response.status == PayloadStatusEnum.VALID, (
            f"Block was rejected by engine_newPayloadV{new_payload_version}: "
            f"{new_payload_response.status}"
        )

        fcu_response = self.engine_rpc.forkchoice_updated(
            ForkchoiceState(
                head_block_hash=payload_response.execution_payload.block_hash
            ),
            None,
            version=fcu_version,
        )
        assert fcu_response.payload_status.status == PayloadStatusEnum.VALID, (
            "engine_forkchoiceUpdated rejected the built payload: "
            f"{fcu_response.payload_status.status}"
        )

    def _fetch_receipts(
        self, txs: List[Transaction]
    ) -> List[TransactionReceipt]:
        """Fetch receipts for each transaction. TODO: batch via JSON-RPC."""
        receipts: List[TransactionReceipt] = []
        for tx in txs:
            receipt_data = self.eth_rpc.get_transaction_receipt(tx.hash)
            if receipt_data is None:
                raise RuntimeError(
                    f"No receipt found for transaction {tx.hash}"
                )
            receipts.append(TransactionReceipt.model_validate(receipt_data))
        return receipts

    def _build_result(
        self,
        *,
        built_payload: Any,
        execution_requests: List[Bytes] | None,
        receipts: List[TransactionReceipt],
        withdrawals: List[Withdrawal] | None,
        block_fork: Fork,
    ) -> Result:
        """Assemble a ``Result`` from the client-built payload + receipts."""
        withdrawals_root: Hash | None = None
        if block_fork.header_withdrawals_required():
            withdrawals_root = Hash(Withdrawal.list_root(withdrawals or []))

        requests: List[Bytes] | None = None
        requests_hash: Hash | None = None
        if block_fork.header_requests_required():
            requests = list(execution_requests or [])
            requests_hash = Hash(
                Requests(requests_lists=list(requests))
            )

        block_access_list_hash: Hash | None = None
        bal_rlp = getattr(built_payload, "block_access_list", None)
        if bal_rlp is not None:
            block_access_list_hash = Hash(
                BlockAccessList.from_rlp(bal_rlp).rlp.keccak256()
            )

        return Result(
            state_root=built_payload.state_root,
            ommers_hash=None,
            transactions_trie=Hash(0),  # overridden downstream
            receipts_root=built_payload.receipts_root,
            logs_hash=Hash(0),  # not surfaced downstream via FixtureHeader
            logs_bloom=built_payload.logs_bloom,
            receipts=receipts,
            rejected_transactions=[],
            gas_used=built_payload.gas_used,
            base_fee_per_gas=built_payload.base_fee_per_gas,
            withdrawals_root=withdrawals_root,
            excess_blob_gas=built_payload.excess_blob_gas,
            blob_gas_used=built_payload.blob_gas_used,
            requests_hash=requests_hash,
            requests=requests,
            block_access_list=bal_rlp,
            block_access_list_hash=block_access_list_hash,
            block_exception=None,
            traces=None,
            opcode_count=None,
        )
