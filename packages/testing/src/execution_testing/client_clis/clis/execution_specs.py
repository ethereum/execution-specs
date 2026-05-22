"""
Ethereum Specs EVM Transition Tool Interface.
"""

import tempfile
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional

from typing_extensions import override

from execution_testing.base_types import Bytes
from execution_testing.client_clis.cli_types import (
    MaterializedAlloc,
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
    from ethereum_spec_tools.evm_tools.t8n import ForkCache


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
            from ethereum_spec_tools.evm_tools.t8n import ForkCache

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
        from ethereum_spec_tools.evm_tools.utils import get_supported_forks

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

        The testing pydantic types flow into ``T8N`` directly via the
        ``t8n_data`` kwarg — no JSON serialize / parse round-trip — and
        the result is read out of ``T8N``'s in-memory state.
        """
        from ethereum_spec_tools.evm_tools import create_parser
        from ethereum_spec_tools.evm_tools.t8n import T8N

        del slow_request, profiler

        temp_dir = tempfile.TemporaryDirectory()
        t8n_args = [
            "t8n",
            f"--output.basedir={temp_dir.name}",
            f"--state.fork={transition_tool_data.fork_name}",
            f"--state.chainid={transition_tool_data.chain_id}",
            f"--state.reward={transition_tool_data.reward}",
        ]
        if transition_tool_data.state_test:
            t8n_args.append("--state-test")
        if self.supports_opcode_count:
            t8n_args.append("--opcode.count=stdout")

        if self.trace:
            t8n_args.extend(
                [
                    "--trace",
                    "--trace.memory",
                    "--trace.returndata",
                ]
            )

        parser = create_parser()
        t8n_options = parser.parse_args(t8n_args)

        t8n_input = transition_tool_data.to_input()
        t8n = T8N(
            t8n_options,
            StringIO(),
            StringIO(),
            self.fork_cache,
            t8n_data=t8n_input,
            exception_mapper=self.exception_mapper,
        )
        t8n.run()

        # The post-state alloc is already materialized in memory —
        # hand it over as a ``MaterializedAlloc`` rather than wrapping
        # it in a ``LazyAllocJson`` with a fake ``raw={}`` placeholder.
        # Consumers use ``.get()`` to retrieve the alloc.
        output = TransitionToolOutput(
            alloc=MaterializedAlloc(
                alloc=t8n.alloc,
                _state_root=t8n.result.state_root,
            ),
            result=t8n.result,
            body=Bytes(t8n.body),
        )

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "input/alloc.json": t8n_input.alloc,
                    "input/env.json": t8n_input.env,
                    "input/txs.json": [
                        tx.model_dump(mode="json", **model_dump_config)
                        for tx in t8n_input.txs
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
    }
