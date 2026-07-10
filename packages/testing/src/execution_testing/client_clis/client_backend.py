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
    DebugRPC,
    EngineRPC,
    EthRPC,
    TestingRPC,
    Web3RPC,
)
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    GetPayloadResponse,
    PayloadAttributes,
    PayloadStatusEnum,
)
from execution_testing.test_types import Requests, Transaction, Withdrawal
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

# JS tracer for ``debug_traceBlockByHash`` that tallies executed opcodes
# per transaction. There is no built-in opcode-count tracer, so we count
# ``log.op`` names ourselves and return the aggregate dict. Used by
# fill-stateful's ``--extract-opcode-count`` to populate
# ``_info.metadata.opcode_count``.
OPCODE_COUNT_TRACER_JS = (
    "{"
    "counts: {}, "
    "step: function(log) { "
    "var op = log.op.toString(); "
    "this.counts[op] = (this.counts[op] || 0) + 1; "
    "}, "
    "fault: function() {}, "
    "result: function() { return this.counts; }"
    "}"
)


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
    ) -> None:
        """Initialize with the RPC clients and the session fork."""
        self.testing_rpc = testing_rpc
        self.engine_rpc = engine_rpc
        self.eth_rpc = eth_rpc
        self.fork = fork
        # Optional debug namespace + flag for --extract-opcode-count: when
        # enabled, each built block is traced via debug_traceBlockByHash.
        self.debug_rpc = debug_rpc
        self.extract_opcode_count = extract_opcode_count
        # Set once a client's JS opcode tracer is found to yield nothing (e.g.
        # besu has no JS tracer), so later blocks skip straight to struct logs.
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
        """
        No-op — the singular ``opcode_count`` accumulator is unused.

        Stateful fill records per-payload opcode counts in
        ``_info.metadata.opcode_counts`` (via ``make_stateful_fixture``),
        not the filler's aggregate ``opcode_count``; ``opcode_count`` stays
        ``None`` so that key is not emitted.
        """
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

        receipts = self._fetch_receipts(txs)
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

    def extract_block_opcode_count(
        self, block_hash: Hash
    ) -> OpcodeCount | None:
        """
        Trace a finalized block via ``debug_traceBlockByHash`` and tally
        executed opcodes across its transactions.

        Returns ``None`` when ``--extract-opcode-count`` is off or no
        ``debug`` RPC is wired — so callers can invoke it unconditionally
        and it stays free when disabled. Called per execution-phase block
        by ``make_stateful_fixture``. The tracer runs a full re-execution
        of the block, so it is opt-in and can be slow on large blocks.

        Uses a client-side JS opcode-counting tracer where supported
        (geth/nethermind/erigon/reth) — cheap, since only the aggregate
        counts cross the wire. Clients without JS tracers (besu) return
        nothing, so we fall back to the universally-supported struct-log
        tracer and count ``structLogs[].op`` here. Struct logs return one
        entry per opcode step, so they are heavier; the fallback is cached
        per client to avoid re-probing the JS tracer on every block.

        Failures are non-fatal: a trace RPC error or an unrecognized
        opcode name is logged and skipped rather than aborting the fill,
        since this is an opt-in analysis feature.
        """
        if not self.extract_opcode_count or self.debug_rpc is None:
            return None

        if not self._js_tracer_unsupported:
            counts = self._count_via_js_tracer(block_hash)
            if counts:
                return OpcodeCount.model_validate(counts)
            # None (RPC error, e.g. an unknown JS tracer) or {} (empty): this
            # client has no usable JS opcode tracer — fall back to struct logs.
            logger.info(
                "opcode trace: JS tracer unavailable; falling back to struct "
                "logs for this client"
            )
            self._js_tracer_unsupported = True

        counts = self._count_via_struct_logs(block_hash)
        if counts is None:
            return None
        return OpcodeCount.model_validate(counts)

    def _count_via_js_tracer(self, block_hash: Hash) -> Dict[str, int] | None:
        """
        Count opcodes with the client-side JS tracer, aggregating the
        per-tx ``{opcode: count}`` maps it returns. ``None`` on RPC error.
        """
        assert self.debug_rpc is not None
        try:
            traces = self.debug_rpc.trace_block_by_hash(
                str(block_hash),
                {"tracer": OPCODE_COUNT_TRACER_JS},
            )
        except Exception as e:
            # Expected for clients without a JS tracer (e.g. besu); the caller
            # falls back to struct logs.
            logger.warning(
                f"opcode JS tracer failed for block {block_hash}: {e}"
            )
            return None
        counts: Dict[str, int] = {}
        for entry in traces or []:
            if not isinstance(entry, dict):
                continue
            tx_counts = entry.get("result")
            if not isinstance(tx_counts, dict):
                continue
            for opcode, count in tx_counts.items():
                key = self._normalize_opcode_name(opcode)
                if key is None:
                    continue
                counts[key] = counts.get(key, 0) + int(count)
        return counts

    def _count_via_struct_logs(
        self, block_hash: Hash
    ) -> Dict[str, int] | None:
        """
        Count opcodes from the default struct-log tracer, which every
        client implements. Stack/memory/storage are disabled to keep each
        step small (still one entry per executed opcode, so the response is
        large for gas-heavy blocks). ``None`` on RPC error.
        """
        assert self.debug_rpc is not None
        try:
            traces = self.debug_rpc.trace_block_by_hash(
                str(block_hash),
                {
                    "disableStack": True,
                    "disableMemory": True,
                    "disableStorage": True,
                },
            )
        except Exception as e:
            logger.warning(
                f"opcode struct-log trace failed for block {block_hash}: "
                f"{e}; skipping opcode count for this block"
            )
            return None
        counts: Dict[str, int] = {}
        for entry in traces or []:
            if not isinstance(entry, dict):
                continue
            # Most clients wrap each tx as {"result": {...}}; some return the
            # struct-log result directly.
            result = entry.get("result")
            if not isinstance(result, dict):
                result = entry
            struct_logs = result.get("structLogs")
            for step in struct_logs or []:
                if not isinstance(step, dict):
                    continue
                op = step.get("op")
                if not op:
                    continue
                key = self._normalize_opcode_name(op)
                if key is None:
                    continue
                counts[key] = counts.get(key, 0) + 1
        return counts

    @staticmethod
    def _normalize_opcode_name(name: str) -> str | None:
        """
        Map a tracer opcode name to one ``OpcodeCount`` accepts.

        Mnemonics (``PUSH1``) and hex (``0x0c``) pass through. Some clients
        emit non-canonical casing (nethermind returns ``calldatasize`` /
        ``pusH1``), so an upper-cased retry is attempted. Geth emits
        ``"opcode 0xNN not defined"`` for undefined opcodes — reduce that
        to the bare ``0xNN`` that validates as an ``UndefinedOpcode``.
        Anything still unrecognized is logged and dropped (returns
        ``None``) so one stray name never aborts the whole fill.
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
