"""EthereumJS Transition tool interface."""

import re
from pathlib import Path
from typing import ClassVar, Dict, Optional

from ethereum_test_exceptions import (
    BlockException,
    EOFException,
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
)
from ethereum_test_forks import Fork

from ..transition_tool import TransitionTool


class EthereumJSTransitionTool(TransitionTool):
    """EthereumJS Transition tool interface wrapper class."""

    default_binary = Path("ethereumjs-t8ntool.sh")
    detect_binary_pattern = re.compile(r"^ethereumjs t8n\b")
    version_flag: str = "--version"
    t8n_use_stream = False

    binary: Path
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the EthereumJS Transition tool interface."""
        super().__init__(exception_mapper=EthereumJSExceptionMapper(), binary=binary, trace=trace)

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool.
        Currently, EthereumJS-t8n provides no way to determine supported forks.
        """
        return True


class EthereumJSExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by EthereumJS."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "would exceed maximum allowance"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "Invalid 4844 transactions: undefined"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "tx unable to pay base fee (EIP-1559 tx)"
        ),
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "maxFeePerGas cannot be less than maxPriorityFeePerGas"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "versioned hash does not start with KZG commitment version"
        ),
        # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: "exceed maximum allowance",
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "tx should contain at least one blob",
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: "Invalid EIP-4844 transaction",
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            'tx should have a "to" field and cannot be used to create contracts'
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "Invalid EIP-7702 transaction: authorization list is empty"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: "is lower than the minimum gas limit of",
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "the initcode size of this transaction is too large"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            'tx should have a "to" field and cannot be used to create contracts'
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            "sender doesn't have enough funds to send tx"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: "the tx doesn't have the correct nonce",
        TransactionException.INVALID_DEPOSIT_EVENT_LAYOUT: "Error verifying block while running",
        BlockException.INCORRECT_EXCESS_BLOB_GAS: "Invalid 4844 transactions",
        BlockException.INVALID_RECEIPTS_ROOT: "invalid receipttrie",
        # TODO EVMONE needs to differentiate when the section is missing in the header or body
        EOFException.MISSING_STOP_OPCODE: "err: no_terminating_instruction",
        EOFException.MISSING_CODE_HEADER: "err: code_section_missing",
        EOFException.MISSING_TYPE_HEADER: "err: type_section_missing",
        # TODO EVMONE these exceptions are too similar, this leeds to ambiguity
        EOFException.MISSING_TERMINATOR: "err: header_terminator_missing",
        EOFException.MISSING_HEADERS_TERMINATOR: "err: section_headers_not_terminated",
        EOFException.INVALID_VERSION: "err: eof_version_unknown",
        EOFException.INVALID_NON_RETURNING_FLAG: "err: invalid_non_returning_flag",
        EOFException.INVALID_MAGIC: "err: invalid_prefix",
        EOFException.INVALID_FIRST_SECTION_TYPE: "err: invalid_first_section_type",
        EOFException.INVALID_SECTION_BODIES_SIZE: "err: invalid_section_bodies_size",
        EOFException.INVALID_TYPE_SECTION_SIZE: "err: invalid_type_section_size",
        EOFException.INCOMPLETE_SECTION_SIZE: "err: incomplete_section_size",
        EOFException.INCOMPLETE_SECTION_NUMBER: "err: incomplete_section_number",
        EOFException.TOO_MANY_CODE_SECTIONS: "err: too_many_code_sections",
        EOFException.ZERO_SECTION_SIZE: "err: zero_section_size",
        EOFException.MISSING_DATA_SECTION: "err: data_section_missing",
        EOFException.UNDEFINED_INSTRUCTION: "err: undefined_instruction",
        EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT: "err: inputs_outputs_num_above_limit",
        EOFException.UNREACHABLE_INSTRUCTIONS: "err: unreachable_instructions",
        EOFException.INVALID_RJUMP_DESTINATION: "err: invalid_rjump_destination",
        EOFException.UNREACHABLE_CODE_SECTIONS: "err: unreachable_code_sections",
        EOFException.STACK_UNDERFLOW: "err: stack_underflow",
        EOFException.MAX_STACK_INCREASE_ABOVE_LIMIT: "err: max_stack_increase_above_limit",
        EOFException.STACK_HIGHER_THAN_OUTPUTS: "err: stack_higher_than_outputs_required",
        EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS: (
            "err: jumpf_destination_incompatible_outputs"
        ),
        EOFException.INVALID_MAX_STACK_INCREASE: "err: invalid_max_stack_increase",
        EOFException.INVALID_DATALOADN_INDEX: "err: invalid_dataloadn_index",
        EOFException.TRUNCATED_INSTRUCTION: "err: truncated_instruction",
        EOFException.TOPLEVEL_CONTAINER_TRUNCATED: "err: toplevel_container_truncated",
        EOFException.ORPHAN_SUBCONTAINER: "err: unreferenced_subcontainer",
        EOFException.CONTAINER_SIZE_ABOVE_LIMIT: "err: container_size_above_limit",
        EOFException.INVALID_CONTAINER_SECTION_INDEX: "err: invalid_container_section_index",
        EOFException.INCOMPATIBLE_CONTAINER_KIND: "err: incompatible_container_kind",
        EOFException.STACK_HEIGHT_MISMATCH: "err: stack_height_mismatch",
        EOFException.TOO_MANY_CONTAINERS: "err: too_many_container_sections",
        EOFException.INVALID_CODE_SECTION_INDEX: "err: invalid_code_section_index",
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"tx causes total blob gas of \d+ to exceed maximum blob gas per block of \d+|"
            r"tx can contain at most \d+ blobs"
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            r"tx causes total blob gas of \d+ to exceed maximum blob gas per block of \d+|"
            r"tx can contain at most \d+ blobs"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            r"blob tx used but field env.ExcessBlobGas missing|EIP-4844 not enabled on Common"
        ),
        BlockException.BLOB_GAS_USED_ABOVE_LIMIT: r"invalid blobGasUsed expected=\d+ actual=\d+",
        BlockException.INCORRECT_BLOB_GAS_USED: r"invalid blobGasUsed expected=\d+ actual=\d+",
        BlockException.INVALID_BLOCK_HASH: (
            r"Invalid blockHash, expected: 0x[0-9a-f]+, received: 0x[0-9a-f]+"
        ),
        BlockException.INVALID_REQUESTS: r"Unknown request identifier|invalid requestshash",
    }
