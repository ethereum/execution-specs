"""
Evmone eof exceptions ENUM -> str mapper
"""

from dataclasses import dataclass

from bidict import frozenbidict

from .exceptions import EOFException


@dataclass
class ExceptionMessage:
    """Defines a mapping between an exception and a message."""

    exception: EOFException
    message: str


class EvmoneExceptionMapper:
    """
    Translate between EEST exceptions and error strings returned by evmone.
    """

    _mapping_data = (
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
        ExceptionMessage(EOFException.INVALID_TYPE_SECTION_SIZE, "err: invalid_type_section_size"),
        ExceptionMessage(EOFException.INCOMPLETE_SECTION_SIZE, "err: incomplete_section_size"),
        ExceptionMessage(EOFException.INCOMPLETE_SECTION_NUMBER, "err: incomplete_section_number"),
        ExceptionMessage(EOFException.TOO_MANY_CODE_SECTIONS, "err: too_many_code_sections"),
        ExceptionMessage(EOFException.ZERO_SECTION_SIZE, "err: zero_section_size"),
        ExceptionMessage(EOFException.MISSING_DATA_SECTION, "err: data_section_missing"),
        ExceptionMessage(EOFException.UNDEFINED_INSTRUCTION, "err: undefined_instruction"),
        ExceptionMessage(
            EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT, "err: inputs_outputs_num_above_limit"
        ),
        ExceptionMessage(EOFException.UNREACHABLE_INSTRUCTIONS, "err: unreachable_instructions"),
        ExceptionMessage(EOFException.INVALID_RJUMP_DESTINATION, "err: invalid_rjump_destination"),
        ExceptionMessage(EOFException.UNREACHABLE_CODE_SECTIONS, "err: unreachable_code_sections"),
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
        ExceptionMessage(EOFException.INVALID_MAX_STACK_HEIGHT, "err: invalid_max_stack_height"),
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
            EOFException.INVALID_CONTAINER_SECTION_INDEX, "err: invalid_container_section_index"
        ),
        ExceptionMessage(
            EOFException.INCOMPATIBLE_CONTAINER_KIND, "err: incompatible_container_kind"
        ),
    )

    def __init__(self) -> None:
        assert len(set(entry.exception for entry in self._mapping_data)) == len(
            self._mapping_data
        ), "Duplicate exception in _mapping_data"
        assert len(set(entry.message for entry in self._mapping_data)) == len(
            self._mapping_data
        ), "Duplicate message in _mapping_data"
        self.exception_to_message_map: frozenbidict = frozenbidict(
            {entry.exception: entry.message for entry in self._mapping_data}
        )

    def exception_to_message(self, exception: EOFException) -> str:
        """Takes an EOFException and returns a formatted string."""
        message = self.exception_to_message_map.get(
            exception,
            f"No message defined for {exception}; please add it to {self.__class__.__name__}",
        )
        return message

    def message_to_exception(self, exception_string: str) -> EOFException:
        """Takes a string and tries to find matching exception"""
        # TODO inform tester where to add the missing exception if get uses default
        exception = self.exception_to_message_map.inverse.get(
            exception_string, EOFException.UNDEFINED_EXCEPTION
        )
        return exception
