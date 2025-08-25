"""
Ethereum Specs EVM Transition Tool Interface.
"""
import json
import tempfile
from io import StringIO
from typing import Any, ClassVar, Dict, Optional

from ethereum_clis.file_utils import dump_files_to_directory
from ethereum_clis.transition_tool import TransitionTool, model_dump_config
from ethereum_clis.types import TransitionToolOutput
from ethereum_test_exceptions import (
    BlockException,
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
)
from ethereum_test_forks import Fork

import ethereum
from ethereum_spec_tools.evm_tools import create_parser
from ethereum_spec_tools.evm_tools.t8n import T8N
from ethereum_spec_tools.evm_tools.utils import get_supported_forks

from ..transition_tool import TransitionTool


class ExecutionSpecsTransitionTool(TransitionTool):
    """Implementation of the EELS T8N for execution-spec-tests."""

    def __init__(
        self,
        *,
        trace: bool = False,
    ):
        """Initialize the EELS Transition Tool interface."""
        self.exception_mapper = ExecutionSpecsExceptionMapper()
        self.trace = trace
        self._info_metadata: Optional[Dict[str, Any]] = {}

    def version(self) -> str:
        """Version of the t8n tool."""
        return ethereum.__version__

    def is_fork_supported(self, fork: Fork) -> bool:
        """Return True if the fork is supported by the tool."""
        return fork.transition_tool_name() in get_supported_forks()

    def evaluate(
        self,
        *,
        transition_tool_data: TransitionTool.TransitionToolData,
        debug_output_path: str = "",
        slow_request: bool = False,  # noqa: U100, F841
    ) -> TransitionToolOutput:
        """
        Evaluate using the EELS T8N entry point.
        """
        request_data = transition_tool_data.get_request_data()
        request_data_json = request_data.model_dump(
            mode="json", **model_dump_config
        )

        t8n_args = [
            "t8n",
            "--input.alloc=stdin",
            "--input.env=stdin",
            "--input.txs=stdin",
            "--output.result=stdout",
            "--output.body=stdout",
            "--output.alloc=stdout",
            f"--state.fork={request_data_json['state']['fork']}",
            f"--state.chainid={request_data_json['state']['chainid']}",
            f"--state.reward={request_data_json['state']['reward']}",
        ]

        if transition_tool_data.state_test:
            t8n_args.append("--state-test")

        temp_dir = tempfile.TemporaryDirectory()
        if self.trace:
            t8n_args.extend(
                [
                    "--trace",
                    "--trace.memory",
                    "--trace.returndata",
                    f"--output.basedir={temp_dir.name}",
                ]
            )

        parser = create_parser()
        t8n_options = parser.parse_args(t8n_args)

        out_stream = StringIO()

        in_stream = StringIO(json.dumps(request_data_json["input"]))

        t8n = T8N(t8n_options, out_stream, in_stream)
        t8n.run()

        output_dict = json.loads(out_stream.getvalue())
        output: TransitionToolOutput = TransitionToolOutput.model_validate(
            output_dict, context={"exception_mapper": self.exception_mapper}
        )

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "input/alloc.json": request_data.input.alloc,
                    "input/env.json": request_data.input.env,
                    "input/txs.json": [
                        tx.model_dump(mode="json", **model_dump_config)
                        for tx in request_data.input.txs
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


class ExecutionSpecsExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by ExecutionSpecs."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: "EmptyAuthorizationListError",
        TransactionException.SENDER_NOT_EOA: "InvalidSenderError",
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "TransactionTypeContractCreationError("
            "'transaction type `SetCodeTransaction` not allowed to create contracts')"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: "InsufficientBalanceError",
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "BlobGasLimitExceededError"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "InsufficientMaxFeePerBlobGasError"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "module 'ethereum.shanghai.transactions' has no attribute 'BlobTransaction'"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "'ethereum.cancun.transactions' has no attribute 'SetCodeTransaction'"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "InvalidBlobVersionedHashError"
        ),
        # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: "BlobCountExceededError",
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "NoBlobDataError",
        TransactionException.INTRINSIC_GAS_TOO_LOW: "InsufficientTransactionGasError",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: "InsufficientTransactionGasError",
        TransactionException.INITCODE_SIZE_EXCEEDED: "InitCodeTooLargeError",
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "PriorityFeeGreaterThanMaxFeeError"
        ),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: "NonceMismatchError('nonce too high')",
        TransactionException.NONCE_MISMATCH_TOO_LOW: "NonceMismatchError('nonce too low')",
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "TransactionTypeContractCreationError("
            "'transaction type `BlobTransaction` not allowed to create contracts')"
        ),
        TransactionException.NONCE_IS_MAX: "NonceOverflowError",
        TransactionException.GAS_ALLOWANCE_EXCEEDED: "GasUsedExceedsLimitError",
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: "TransactionGasLimitExceededError",
        BlockException.SYSTEM_CONTRACT_EMPTY: "System contract address",
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: "call failed:",
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: "deposit",
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            r"InsufficientMaxFeePerGasError|InvalidBlock"  # Temporary solution for issue #1981.
        ),
    }
