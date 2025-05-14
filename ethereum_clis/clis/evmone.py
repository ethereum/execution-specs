"""Evmone Transition tool interface."""

import re
from pathlib import Path
from typing import ClassVar, Dict, Optional

from ethereum_test_exceptions import (
    EOFException,
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
)
from ethereum_test_forks import Fork

from ..transition_tool import TransitionTool


class EvmOneTransitionTool(TransitionTool):
    """Evmone `evmone-t8n` Transition tool interface wrapper class."""

    default_binary = Path("evmone-t8n")
    detect_binary_pattern = re.compile(r"^evmone-t8n\b")
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
        """Initialize the Evmone Transition tool interface."""
        super().__init__(exception_mapper=EvmoneExceptionMapper(), binary=binary, trace=trace)

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool.
        Currently, evmone-t8n provides no way to determine supported forks.
        """
        return True


class EvmoneExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by Evmone."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.SENDER_NOT_EOA: "sender not an eoa:",
        TransactionException.GAS_ALLOWANCE_EXCEEDED: "gas limit reached",
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "max priority fee per gas higher than max fee per gas"
        ),
        TransactionException.NONCE_IS_MAX: "nonce has max value:",
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: "set code transaction must ",
        TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE: "invalid authorization signature",
        TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE_S_TOO_HIGH: (
            "authorization signature s value too high"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: "empty authorization list",
        TransactionException.INTRINSIC_GAS_TOO_LOW: "intrinsic gas too low",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: "intrinsic gas too low",
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: "blob gas limit exceeded",
        TransactionException.INITCODE_SIZE_EXCEEDED: "max initcode size exceeded",
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            "insufficient funds for gas * price + value"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "max fee per gas less than block base fee"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "max blob fee per gas less than block base fee"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: "transaction type not supported",
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: "invalid blob hash version",
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: "blob gas limit exceeded",
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "empty blob hashes list",
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "blob transaction must not be a create transaction"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: "nonce too low",
        TransactionException.NONCE_MISMATCH_TOO_HIGH: "nonce too high",
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
        EOFException.STACK_OVERFLOW: "err: stack_overflow",
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
        EOFException.AMBIGUOUS_CONTAINER_KIND: "err: ambiguous_container_kind",
        EOFException.STACK_HEIGHT_MISMATCH: "err: stack_height_mismatch",
        EOFException.TOO_MANY_CONTAINERS: "err: too_many_container_sections",
        EOFException.INVALID_CODE_SECTION_INDEX: "err: invalid_code_section_index",
        EOFException.CALLF_TO_NON_RETURNING: "err: callf_to_non_returning_function",
        EOFException.EOFCREATE_WITH_TRUNCATED_CONTAINER: "err: eofcreate_with_truncated_container",
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {}
