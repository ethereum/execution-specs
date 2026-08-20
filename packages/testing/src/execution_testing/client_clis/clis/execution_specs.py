"""
Ethereum Specs EVM Transition Tool Interface.
"""

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional

from typing_extensions import override

from execution_testing.client_clis.cli_types import (
    OpcodeCount,
    TransitionToolOutput,
)
from execution_testing.client_clis.file_utils import (
    dump_files_to_directory,
)
from execution_testing.client_clis.transition_tool import (
    Profiler,
    TransitionTool,
    model_dump_config,
)
from execution_testing.exceptions import (
    BlockException,
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
)
from execution_testing.forks import Fork

if TYPE_CHECKING:
    from execution_testing.evm_tools.t8n import ForkCache


class ExecutionSpecsTransitionTool(TransitionTool):
    """Implementation of the EELS T8N for execution-spec-tests."""

    supports_opcode_count: ClassVar[bool] = True
    supports_blob_params: ClassVar[bool] = True

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the EELS Transition Tool interface."""
        del binary  # EELS doesn't use an external binary
        self.exception_mapper = ExecutionSpecsExceptionMapper()
        self.trace = trace
        self._info_metadata: Optional[Dict[str, Any]] = {}
        # Defer importing the `ethereum` package (see `fork_cache` and
        # `version`) until the tool is actually used. The tool is constructed
        # during `pytest_configure`, which on xdist workers runs *before*
        # pytest-cov starts the worker's coverage session; importing `ethereum`
        # here would make coverage report it as "module-not-measured".
        self._fork_cache: Optional["ForkCache"] = None

    @property
    def fork_cache(self) -> "ForkCache":
        """Lazily import and instantiate the EELS fork cache on first use."""
        if self._fork_cache is None:
            from execution_testing.evm_tools.t8n import ForkCache

            self._fork_cache = ForkCache()
        return self._fork_cache

    @override
    def shutdown(self) -> None:
        if self._fork_cache is not None:
            self._fork_cache.__exit__()

    def version(self) -> str:
        """Version of the t8n tool."""
        # Use package metadata rather than `ethereum.__version__` to avoid
        # importing `ethereum` here (see `__init__` for why it must stay lazy).
        from importlib.metadata import version

        return version("ethereum-execution")

    def is_fork_supported(self, fork: Fork) -> bool:
        """Return True if the fork is supported by the tool."""
        from ethereum_spec_tools.utils import get_supported_forks

        return fork.transition_tool_name() in get_supported_forks()

    def _evaluate(
        self,
        *,
        transition_tool_data: TransitionTool.TransitionToolData,
        debug_output_path: Path | None,
        slow_request: bool,
        profiler: Profiler,
    ) -> TransitionToolOutput:
        """
        Evaluate using the EELS T8N entry point in-process.

        ``transition_tool_data`` is handed to ``T8N`` as-is — fork,
        chain_id, reward, state_test, blob_schedule all flow through
        — and ``T8N.run()`` returns the ``TransitionToolOutput``
        directly.
        """
        from execution_testing.evm_tools.t8n import T8N
        from execution_testing.evm_tools.t8n.evm_trace.count import (
            CountTracer,
        )
        from execution_testing.evm_tools.t8n.evm_trace.eip3155 import (
            Eip3155Tracer,
        )
        from execution_testing.evm_tools.t8n.evm_trace.group import (
            GroupTracer,
        )

        del slow_request, profiler

        temp_dir = tempfile.TemporaryDirectory()

        tracers = None
        if self.trace:
            # TODO: Eip3155 traces still round-trip through tempfile
            # JSON — the tracer writes one ``trace-<i>.jsonl`` per tx
            # to ``output_basedir`` and ``collect_traces`` reads them
            # back. Same JSON round-trip we eliminated for alloc /
            # result / body; a follow-up should wire the tracer
            # output through memory like the rest of the in-process
            # path.
            tracers = GroupTracer()
            tracers.add(
                Eip3155Tracer(
                    trace_memory=True,
                    trace_stack=True,
                    trace_return_data=True,
                    output_basedir=temp_dir.name,
                )
            )

        count_tracer = None
        if self.supports_opcode_count:
            count_tracer = CountTracer()
            if tracers is None:
                tracers = GroupTracer()
            tracers.add(count_tracer)

        t8n = T8N(
            transition_tool_data,
            cache=self.fork_cache,
            tracers=tracers,
            exception_mapper=self.exception_mapper,
        )
        output = t8n.run()

        if count_tracer is not None:
            output.result.opcode_count = OpcodeCount.model_validate(
                count_tracer.results()
            )

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "input/alloc.json": transition_tool_data.alloc,
                    "input/env.json": transition_tool_data.env,
                    "input/txs.json": [
                        tx.model_dump(mode="json", **model_dump_config)
                        for tx in transition_tool_data.txs
                    ],
                },
            )

            dump_files_to_directory(
                debug_output_path,
                {
                    "output/alloc.json": output.alloc,
                    "output/result.json": output.result,
                },
            )

        if self.trace:
            self.collect_traces(
                output.result.receipts, temp_dir, debug_output_path
            )
        temp_dir.cleanup()

        return output

    @classmethod
    def is_installed(cls, binary_path: Optional[Path] = None) -> bool:
        """ExecutionSpecs is always installed."""
        del binary_path
        return True


class ExecutionSpecsExceptionMapper(ExceptionMapper):
    """
    Translate between EEST exceptions and error strings returned by
    ExecutionSpecs.
    """

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "EmptyAuthorizationListError"
        ),
        TransactionException.SENDER_NOT_EOA: "InvalidSenderError",
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "TransactionTypeContractCreationError("
            "'transaction type `SetCodeTransaction` not allowed to "
            "create contracts')"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            "InsufficientBalanceError"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "BlobGasLimitExceededError"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "InsufficientMaxFeePerBlobGasError"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "InvalidBlobVersionedHashError"
        ),
        # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            "BlobCountExceededError"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "NoBlobDataError",
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            "InsufficientTransactionGasError"
        ),
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            "InsufficientTransactionGasError"
        ),
        TransactionException.INVALID_SIGNATURE_VRS: (
            "InvalidSignatureError('bad"
        ),
        TransactionException.INVALID_CHAINID: ("WrongChainId"),
        TransactionException.INITCODE_SIZE_EXCEEDED: "InitCodeTooLargeError",
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "PriorityFeeGreaterThanMaxFeeError"
        ),
        TransactionException.GASPRICE_OVERFLOW: (
            "FeeOverflowError('Max fee per gas too high')"
        ),
        TransactionException.PRIORITY_OVERFLOW: (
            "FeeOverflowError('Max priority fee per gas too high')"
        ),
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW: (
            "MaxCostOverflowError"
        ),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: (
            "NonceMismatchError('nonce too high')"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: (
            "NonceMismatchError('nonce too low')"
        ),
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "TransactionTypeContractCreationError("
            "'transaction type `BlobTransaction` not allowed to "
            "create contracts')"
        ),
        TransactionException.NONCE_IS_MAX: "NonceOverflowError",
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            "GasUsedExceedsLimitError"
        ),
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            "TransactionGasLimitExceededError"
        ),
        BlockException.SYSTEM_CONTRACT_EMPTY: "System contract address",
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: "call failed:",
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: "deposit",
        BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED: (
            "Block access list exceeds gas limit"
        ),
        TransactionException.LOG_MISMATCH: "LogMismatchError",
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT: (
            "InvalidFrameError"
        ),
        TransactionException.TYPE_6_INVALID_SIGNATURE: (
            "InvalidSignatureError"
        ),
        TransactionException.TYPE_6_INVALID_FRAME_EXECUTION: (
            "FrameTransactionExecutionError"
        ),
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {
        # Temporary solution for issue #1981.
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            r"InsufficientMaxFeePerGasError|InvalidBlock"
        ),
        TransactionException.TYPE_1_TX_PRE_FORK: (
            r"module '.*transactions' has no attribute "
            r"'AccessListTransaction'|"
            r"transaction type 1 is not supported in .*"
        ),
        TransactionException.TYPE_2_TX_PRE_FORK: (
            r"'.*transactions' has no attribute 'FeeMarketTransaction'|"
            r"transaction type 2 is not supported in .*"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            r"module '.*transactions' has no attribute 'BlobTransaction'|"
            r"transaction type 3 is not supported in .*"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            r"'.*transactions' has no attribute 'SetCodeTransaction'|"
            r"transaction type 4 is not supported in .*"
        ),
        # Frame-count and blob-fee violations are static frame
        # transaction format errors, but ExecutionSpecs raises them as
        # dedicated exception classes rather than InvalidFrameError.
        # The "invalid frame ... field" messages come from the t8n
        # transaction loader for field values the transaction types
        # reject as they are constructed (undefined modes, flags, or
        # schemes), which on a real client fail to decode.
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT: (
            r"FrameCountError|InvalidMaxFeePerBlobGasError"
            r"|invalid frame (signature )?field"
        ),
    }
