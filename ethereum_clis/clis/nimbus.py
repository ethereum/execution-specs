"""Nimbus Transition tool interface."""

import re
import subprocess
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


class NimbusTransitionTool(TransitionTool):
    """Nimbus `evm` Transition tool interface wrapper class."""

    default_binary = Path("t8n")
    detect_binary_pattern = re.compile(r"^Nimbus-t8n\b")
    version_flag: str = "--version"

    binary: Path
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the Nimbus Transition tool interface."""
        super().__init__(exception_mapper=NimbusExceptionMapper(), binary=binary, trace=trace)
        args = [str(self.binary), "--help"]
        try:
            result = subprocess.run(args, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception(
                f"evm process unexpectedly returned a non-zero status code: {e}."
            ) from e
        except Exception as e:
            raise Exception(f"Unexpected exception calling evm tool: {e}.") from e
        self.help_string = result.stdout

    def version(self) -> str:
        """Get `evm` binary version."""
        if self.cached_version is None:
            self.cached_version = re.sub(r"\x1b\[0m", "", super().version()).strip()

        return self.cached_version

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool.

        If the fork is a transition fork, we want to check the fork it transitions to.
        """
        return fork.transition_tool_name() in self.help_string


class NimbusExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by Nimbus."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "set code transaction must not be a create transaction"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: "invalid tx: not enough cash to send",
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "would exceed maximum allowance"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "max fee per blob gas less than block blob gas fee"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "max fee per gas less than block base fee"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "blob tx used but field env.ExcessBlobGas missing"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "invalid tx: one of blobVersionedHash has invalid version"
        ),
        # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: "exceeds maximum allowance",
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "blob transaction missing blob hashes",
        TransactionException.INTRINSIC_GAS_TOO_LOW: "intrinsic gas too low",
        TransactionException.INITCODE_SIZE_EXCEEDED: "max initcode size exceeded",
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
        EOFException.MAX_STACK_HEIGHT_ABOVE_LIMIT: "err: max_stack_height_above_limit",
        EOFException.STACK_HIGHER_THAN_OUTPUTS: "err: stack_higher_than_outputs_required",
        EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS: (
            "err: jumpf_destination_incompatible_outputs"
        ),
        EOFException.INVALID_MAX_STACK_HEIGHT: "err: invalid_max_stack_height",
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
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {}
