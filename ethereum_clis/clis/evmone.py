"""Evmone Transition tool interface."""

import re
from pathlib import Path
from typing import Optional

from ethereum_test_exceptions import (
    EOFException,
    ExceptionMapper,
    ExceptionMessage,
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

    @property
    def _mapping_data(self):
        return [
            ExceptionMessage(
                TransactionException.TYPE_4_TX_CONTRACT_CREATION,
                "set code transaction must ",
            ),
            ExceptionMessage(
                TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE,
                "invalid authorization signature",
            ),
            ExceptionMessage(
                TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE_S_TOO_HIGH,
                "authorization signature s value too high",
            ),
            ExceptionMessage(
                TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST,
                "empty authorization list",
            ),
            ExceptionMessage(
                TransactionException.INTRINSIC_GAS_TOO_LOW,
                "intrinsic gas too low",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED,
                "lob gas limit exceeded",
            ),
            ExceptionMessage(
                TransactionException.INITCODE_SIZE_EXCEEDED,
                "max initcode size exceeded",
            ),
            ExceptionMessage(
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                "insufficient funds for gas * price + value",
            ),
            ExceptionMessage(
                TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS,
                "max fee per gas less than block base fee",
            ),
            ExceptionMessage(
                TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
                "fee per gas less than block base fee",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_PRE_FORK,
                "transaction type not supported",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH,
                "invalid blob hash version",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED,
                "blob gas limit exceeded",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_ZERO_BLOBS,
                "empty blob hashes list",
            ),
            ExceptionMessage(
                TransactionException.NONCE_MISMATCH_TOO_LOW,
                "nonce too low",
            ),
            ExceptionMessage(
                TransactionException.NONCE_MISMATCH_TOO_HIGH,
                "nonce too high",
            ),
            # TODO EVMONE needs to differentiate when the section is missing in the header or body
            ExceptionMessage(EOFException.MISSING_STOP_OPCODE, "err: no_terminating_instruction"),
            ExceptionMessage(EOFException.MISSING_CODE_HEADER, "err: code_section_missing"),
            ExceptionMessage(EOFException.MISSING_TYPE_HEADER, "err: type_section_missing"),
            # TODO EVMONE these exceptions are too similar, this leeds to ambiguity
            ExceptionMessage(EOFException.MISSING_TERMINATOR, "err: header_terminator_missing"),
            ExceptionMessage(
                EOFException.MISSING_HEADERS_TERMINATOR, "err: section_headers_not_terminated"
            ),
            ExceptionMessage(EOFException.INVALID_VERSION, "err: eof_version_unknown"),
            ExceptionMessage(
                EOFException.INVALID_NON_RETURNING_FLAG, "err: invalid_non_returning_flag"
            ),
            ExceptionMessage(EOFException.INVALID_MAGIC, "err: invalid_prefix"),
            ExceptionMessage(
                EOFException.INVALID_FIRST_SECTION_TYPE, "err: invalid_first_section_type"
            ),
            ExceptionMessage(
                EOFException.INVALID_SECTION_BODIES_SIZE, "err: invalid_section_bodies_size"
            ),
            ExceptionMessage(
                EOFException.INVALID_TYPE_SECTION_SIZE, "err: invalid_type_section_size"
            ),
            ExceptionMessage(EOFException.INCOMPLETE_SECTION_SIZE, "err: incomplete_section_size"),
            ExceptionMessage(
                EOFException.INCOMPLETE_SECTION_NUMBER, "err: incomplete_section_number"
            ),
            ExceptionMessage(EOFException.TOO_MANY_CODE_SECTIONS, "err: too_many_code_sections"),
            ExceptionMessage(EOFException.ZERO_SECTION_SIZE, "err: zero_section_size"),
            ExceptionMessage(EOFException.MISSING_DATA_SECTION, "err: data_section_missing"),
            ExceptionMessage(EOFException.UNDEFINED_INSTRUCTION, "err: undefined_instruction"),
            ExceptionMessage(
                EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT, "err: inputs_outputs_num_above_limit"
            ),
            ExceptionMessage(
                EOFException.UNREACHABLE_INSTRUCTIONS, "err: unreachable_instructions"
            ),
            ExceptionMessage(
                EOFException.INVALID_RJUMP_DESTINATION, "err: invalid_rjump_destination"
            ),
            ExceptionMessage(
                EOFException.UNREACHABLE_CODE_SECTIONS, "err: unreachable_code_sections"
            ),
            ExceptionMessage(EOFException.STACK_UNDERFLOW, "err: stack_underflow"),
            ExceptionMessage(EOFException.STACK_OVERFLOW, "err: stack_overflow"),
            ExceptionMessage(
                EOFException.MAX_STACK_HEIGHT_ABOVE_LIMIT, "err: max_stack_height_above_limit"
            ),
            ExceptionMessage(
                EOFException.STACK_HIGHER_THAN_OUTPUTS, "err: stack_higher_than_outputs_required"
            ),
            ExceptionMessage(
                EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS,
                "err: jumpf_destination_incompatible_outputs",
            ),
            ExceptionMessage(
                EOFException.INVALID_MAX_STACK_HEIGHT, "err: invalid_max_stack_height"
            ),
            ExceptionMessage(EOFException.INVALID_DATALOADN_INDEX, "err: invalid_dataloadn_index"),
            ExceptionMessage(EOFException.TRUNCATED_INSTRUCTION, "err: truncated_instruction"),
            ExceptionMessage(
                EOFException.TOPLEVEL_CONTAINER_TRUNCATED, "err: toplevel_container_truncated"
            ),
            ExceptionMessage(EOFException.ORPHAN_SUBCONTAINER, "err: unreferenced_subcontainer"),
            ExceptionMessage(
                EOFException.CONTAINER_SIZE_ABOVE_LIMIT, "err: container_size_above_limit"
            ),
            ExceptionMessage(
                EOFException.INVALID_CONTAINER_SECTION_INDEX,
                "err: invalid_container_section_index",
            ),
            ExceptionMessage(
                EOFException.INCOMPATIBLE_CONTAINER_KIND, "err: incompatible_container_kind"
            ),
            ExceptionMessage(EOFException.STACK_HEIGHT_MISMATCH, "err: stack_height_mismatch"),
            ExceptionMessage(EOFException.TOO_MANY_CONTAINERS, "err: too_many_container_sections"),
            ExceptionMessage(
                EOFException.INVALID_CODE_SECTION_INDEX, "err: invalid_code_section_index"
            ),
            ExceptionMessage(
                EOFException.CALLF_TO_NON_RETURNING, "err: callf_to_non_returning_function"
            ),
            ExceptionMessage(
                EOFException.EOFCREATE_WITH_TRUNCATED_CONTAINER,
                "err: eofcreate_with_truncated_container",
            ),
        ]
