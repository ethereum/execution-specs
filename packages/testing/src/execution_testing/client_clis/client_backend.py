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

import re
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

from execution_testing.base_types import Bytes, Hash
from execution_testing.exceptions import ExceptionBase, ExceptionMapper
from execution_testing.forks import Fork, TransitionFork
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    BlockNumberType,
    DebugRPC,
    EngineRPC,
    EthRPC,
    TestingRPC,
    Web3RPC,
)
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    GetPayloadResponse,
    JSONRPCError,
    PayloadAttributes,
    PayloadStatusEnum,
)
from execution_testing.test_types import (
    Alloc,
    Requests,
    Transaction,
    Withdrawal,
)
from execution_testing.test_types.block_access_list import BlockAccessList
from execution_testing.test_types.receipt_types import TransactionReceipt

from .cli_types import (
    EnginePayloadMetadata,
    LazyAllocJson,
    OpcodeCount,
    Result,
    Traces,
    TransitionToolOutput,
    validate_opcode,
)
from .transition_tool import TransitionTool

logger = get_logger(__name__)

# Per-tx opcode tally; clients ship no built-in opcode-count tracer.
OPCODE_COUNT_TRACER_JS = """{
    counts: {},
    step: function(log) {
        var op = log.op.toString();
        this.counts[op] = (this.counts[op] || 0) + 1;
    },
    fault: function() {},
    result: function() { return this.counts; }
}"""

# Keep each struct-log step small.
STRUCT_LOG_TRACER_CONFIG = {
    "disableStack": True,
    "disableMemory": True,
    "disableStorage": True,
}

DEFAULT_OPCODE_COUNT_TRACE_TIMEOUT = "1h"


def _normalize_opcode_name(name: str) -> str | None:
    """
    Map a tracer opcode name to one ``OpcodeCount`` accepts.

    Handles non-canonical casing (nethermind) and geth's
    ``"opcode 0xNN not defined"``; unrecognized names are dropped.
    """
    for candidate in (name, name.upper()):
        try:
            validate_opcode(candidate)
            return candidate
        except Exception:
            continue
    match = re.search(r"0x[0-9a-fA-F]+", name)
    if match is not None:
        return match.group(0)
    logger.warning(f"opcode trace: dropping unrecognized {name!r}")
    return None


def _opcode_count_from_js_tracer(traces: Any) -> OpcodeCount:
    """Aggregate the per-tx ``{opcode: count}`` maps the JS tracer emits."""
    counts: Dict[str, int] = {}
    for entry in traces or []:
        if not isinstance(entry, dict):
            continue
        tx_counts = entry.get("result")
        # Clients that ignore the JS tracer echo struct logs.
        if not isinstance(tx_counts, dict) or "structLogs" in tx_counts:
            continue
        for opcode, count in tx_counts.items():
            key = _normalize_opcode_name(opcode)
            if key is None or not isinstance(count, int):
                continue
            counts[key] = counts.get(key, 0) + count
    return OpcodeCount.model_validate(counts)


def _opcode_count_from_struct_logs(traces: Any) -> OpcodeCount:
    """Count ``structLogs[].op`` entries, one per executed opcode."""
    counts: Dict[str, int] = {}
    for entry in traces or []:
        if not isinstance(entry, dict):
            continue
        # Some clients return the struct-log result unwrapped.
        result = entry.get("result")
        if not isinstance(result, dict):
            result = entry
        for step in result.get("structLogs") or []:
            if not isinstance(step, dict):
                continue
            op = step.get("op")
            if not op:
                continue
            key = _normalize_opcode_name(op)
            if key is None:
                continue
            counts[key] = counts.get(key, 0) + 1
    return OpcodeCount.model_validate(counts)


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
    """Raw datadir head, set by the fill-stateful plugin pre-session."""
    start_block: Dict[str, Any] | None
    """Client head after global pre-run setup; per-test chains off this."""

    # t8n-compatibility stubs — fill's filler reads these on the backend.
    opcode_count: OpcodeCount | None = None
    opcode_count_per_block: List[OpcodeCount] | None = None
    output_cache: Any = None
    debug_dump_dir: Path | None = None
    call_counter: int = 0
    _info_metadata: Dict[str, Any]

    # Session fees pinned by the fill-stateful plugin; read by
    # ``make_stateful_fixture`` to size pre-alloc funding.
    gas_price: int = 0
    max_fee_per_gas: int = 0
    max_priority_fee_per_gas: int = 0
    max_fee_per_blob_gas: int = 0

    def __init__(
        self,
        *,
        testing_rpc: TestingRPC,
        engine_rpc: EngineRPC,
        eth_rpc: EthRPC,
        fork: Fork | TransitionFork,
        debug_rpc: DebugRPC | None = None,
        extract_opcode_count: bool = False,
        opcode_count_trace_timeout: str = DEFAULT_OPCODE_COUNT_TRACE_TIMEOUT,
    ) -> None:
        """Initialize with the RPC clients and the session fork."""
        self.testing_rpc = testing_rpc
        self.engine_rpc = engine_rpc
        self.eth_rpc = eth_rpc
        self.fork = fork
        self.debug_rpc = debug_rpc
        self.extract_opcode_count = extract_opcode_count
        self.opcode_count_trace_timeout = opcode_count_trace_timeout
        # Sticky fallback to struct logs (besu has no JS tracer).
        self._js_tracer_unsupported = False
        self.exception_mapper = ClientBackendExceptionMapper()
        self.snapshot_block = None
        self.start_block = None
        self._info_metadata = {}
        self.gas_price = 0
        self.max_fee_per_gas = 0
        self.max_priority_fee_per_gas = 0
        self.max_fee_per_blob_gas = 0
        # Captured for the fixture's ``_info.filling-transition-tool``.
        try:
            self._client_version: str | None = Web3RPC(
                eth_rpc.url
            ).client_version()
        except Exception:  # pragma: no cover — no web3 namespace
            self._client_version = None

    def version(self) -> str:
        """Return an identifier for this backend (used in fixture _info)."""
        if self._client_version:
            return f"ClientBackend[{self._client_version}; fork={self.fork}]"
        return f"ClientBackend[fork={self.fork}]"

    def shutdown(self) -> None:
        """No-op — owned by the fill-stateful plugin."""
        return

    def reset_traces(self) -> None:
        """No-op — traces not supported."""
        return

    def reset_opcode_count(self) -> None:
        """No-op — ``opcode_count`` stays ``None`` so the filler skips it."""
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
        np_version = block_fork.engine_new_payload_version()
        fcu_version = block_fork.engine_forkchoice_updated_version()
        assert np_version is not None
        assert fcu_version is not None

        receipts = self._fetch_receipts(
            txs, get_payload_response.execution_payload.block_hash
        )
        result = self._build_result(
            built_payload=get_payload_response.execution_payload,
            execution_requests=get_payload_response.execution_requests,
            receipts=receipts,
            withdrawals=env.withdrawals,
            block_fork=block_fork,
        )
        alloc = LazyAllocJson(raw={}, _state_root=result.state_root)
        return TransitionToolOutput(
            alloc=alloc,
            result=result,
            engine_payload=EnginePayloadMetadata(
                payload_response=get_payload_response,
                new_payload_version=np_version,
                forkchoice_updated_version=fcu_version,
                parent_beacon_block_root=(
                    payload_attributes.parent_beacon_block_root
                ),
            ),
        )

    def get_post_state_alloc(
        self, expected: Alloc, *, block_number: BlockNumberType = "latest"
    ) -> Alloc:
        """Fetch the post-state that ``expected`` constrains from client."""
        return self.eth_rpc.get_alloc(expected, block_number=block_number)

    def extract_block_opcode_count(
        self, block_hash: Hash
    ) -> OpcodeCount | None:
        """
        Tally executed opcodes for a block via ``debug_traceBlockByHash``.

        ``None`` when ``--extract-opcode-count`` is off or the trace
        fails (logged, never fatal). Prefers the JS tracer; a client
        that rejects it falls back to struct logs for the session,
        while transient errors only skip the block.
        """
        if not self.extract_opcode_count or self.debug_rpc is None:
            return None

        try:
            if not self._js_tracer_unsupported:
                try:
                    traces = self._trace_block(
                        block_hash, {"tracer": OPCODE_COUNT_TRACER_JS}
                    )
                    return _opcode_count_from_js_tracer(traces)
                except JSONRPCError as e:
                    logger.info(f"JS tracer rejected ({e}); using struct logs")
                    self._js_tracer_unsupported = True
            traces = self._trace_block(block_hash, STRUCT_LOG_TRACER_CONFIG)
            return _opcode_count_from_struct_logs(traces)
        except Exception as e:
            logger.warning(f"opcode trace failed for block {block_hash}: {e}")
            return None

    def _trace_block(
        self, block_hash: Hash, tracer_config: Dict[str, Any]
    ) -> Any:
        """Raw ``debug_traceBlockByHash`` call; exceptions propagate."""
        assert self.debug_rpc is not None
        return self.debug_rpc.trace_block_by_hash(
            str(block_hash),
            {"timeout": self.opcode_count_trace_timeout, **tracer_config},
        )

    def _payload_attributes(
        self,
        env: Any,
        block_fork: Fork,
    ) -> PayloadAttributes:
        """Build ``PayloadAttributes`` from the test's environment."""
        withdrawals: List[Withdrawal] | None = None
        if block_fork.header_withdrawals_required():
            withdrawals = list(env.withdrawals or [])
        parent_beacon_block_root: Hash | None = None
        if block_fork.header_beacon_root_required():
            parent_beacon_block_root = Hash(env.parent_beacon_block_root or 0)
        return PayloadAttributes.for_fork(
            block_fork,
            timestamp=int(env.timestamp),
            prev_randao=Hash(env.prev_randao or 0),
            suggested_fee_recipient=env.fee_recipient,
            withdrawals=withdrawals,
            parent_beacon_block_root=parent_beacon_block_root,
        )

    def _finalize(
        self,
        payload_response: GetPayloadResponse,
        *,
        parent_beacon_block_root: Hash | None,
        block_fork: Fork,
    ) -> None:
        """
        Advance the chain with engine_newPayload + forkchoiceUpdated.

        Both calls retry past transient ``SYNCING`` (geth returns it
        under back-to-back chain-advance load); a stuck-SYNCING client
        surfaces as a ``*TimeoutError``.
        """
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

        new_payload_response = self.engine_rpc.new_payload_with_retry(
            *new_payload_args, version=new_payload_version
        )
        assert new_payload_response.status == PayloadStatusEnum.VALID, (
            f"Block was rejected by engine_newPayloadV{new_payload_version}: "
            f"{new_payload_response.status}"
        )

        fcu_response = self.engine_rpc.forkchoice_updated_with_retry(
            forkchoice_state=ForkchoiceState(
                head_block_hash=payload_response.execution_payload.block_hash
            ),
            forkchoice_version=fcu_version,
        )
        assert fcu_response.payload_status.status == PayloadStatusEnum.VALID, (
            "engine_forkchoiceUpdated rejected the built payload: "
            f"{fcu_response.payload_status.status}"
        )

    def _fetch_receipts(
        self,
        txs: List[Transaction],
        block_hash: Hash,
    ) -> List[TransactionReceipt]:
        """
        Fetch all transaction receipts in order.

        Use `eth_getBlockReceipts` for the block, then fetch any receipt it
        did not return with a batched `eth_getTransactionReceipt` fallback.
        Raise an error if any receipt remains missing.
        """
        if not txs:
            return []
        block_receipts: List[dict[str, Any]] = []
        try:
            block_receipts = self.eth_rpc.get_block_receipts(block_hash) or []
        except JSONRPCError as error:
            logger.warning(
                f"eth_getBlockReceipts failed for block {block_hash}: {error}"
            )

        receipt_data_by_hash: Dict[Hash, dict[str, Any]] = {}
        for receipt_data in block_receipts:
            tx_hash = receipt_data.get("transactionHash")
            if tx_hash is not None:
                receipt_data_by_hash[Hash(tx_hash)] = receipt_data

        missing = [
            tx.hash for tx in txs if tx.hash not in receipt_data_by_hash
        ]
        if missing:
            logger.warning(
                f"Block receipts covered {len(txs) - len(missing)} of "
                f"{len(txs)} transactions; fetching the remaining "
                f"{len(missing)} in a batched fallback"
            )
            fetched = self.eth_rpc.get_transaction_receipts(missing)
            for tx_hash, fetched_data in zip(missing, fetched, strict=True):
                if fetched_data is None:
                    raise RuntimeError(
                        f"No receipt found for transaction {tx_hash}"
                    )
                receipt_data_by_hash[tx_hash] = fetched_data

        return [
            TransactionReceipt.model_validate(receipt_data_by_hash[tx.hash])
            for tx in txs
        ]

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
            requests_hash = Hash(Requests(requests_lists=list(requests)))

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
