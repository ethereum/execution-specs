"""
EthereumJS Transition tool interface.
"""

from pathlib import Path
from re import compile
from typing import Optional

from ethereum_test_exceptions import (
    EOFException,
    ExceptionMapper,
    ExceptionMessage,
    TransactionException,
)
from ethereum_test_forks import Fork

from ..transition_tool import TransitionTool


class EthereumJSTransitionTool(TransitionTool):
    """
    EthereumJS Transition tool interface wrapper class.
    """

    default_binary = Path("ethereumjs-t8ntool.sh")
    detect_binary_pattern = compile(r"^ethereumjs t8n\b")
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
        super().__init__(exception_mapper=EthereumJSExceptionMapper(), binary=binary, trace=trace)

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool.
        Currently, EthereumJS-t8n provides no way to determine supported forks.
        """
        return True


class EthereumJSExceptionMapper(ExceptionMapper):
    """
    Translate between EEST exceptions and error strings returned by ethereum-js.
    """

    @property
    def _mapping_data(self):
        return [
            ExceptionMessage(
                TransactionException.TYPE_4_TX_CONTRACT_CREATION,
                "set code transaction must not be a create transaction",
            ),
            ExceptionMessage(
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                "insufficient funds for gas * price + value",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED,
                "would exceed maximum allowance",
            ),
            ExceptionMessage(
                TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
                "max fee per blob gas less than block blob gas fee",
            ),
            ExceptionMessage(
                TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS,
                "max fee per gas less than block base fee",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_PRE_FORK,
                "blob tx used but field env.ExcessBlobGas missing",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH,
                "has invalid hash version",
            ),
            # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
            ExceptionMessage(
                TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED,
                "exceed maximum allowance",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_ZERO_BLOBS,
                "blob transaction missing blob hashes",
            ),
            ExceptionMessage(
                TransactionException.INTRINSIC_GAS_TOO_LOW,
                "is lower than the minimum gas limit of",
            ),
            ExceptionMessage(
                TransactionException.INITCODE_SIZE_EXCEEDED,
                "max initcode size exceeded",
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
        ]
