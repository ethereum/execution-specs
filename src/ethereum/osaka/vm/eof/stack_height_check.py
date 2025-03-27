"""
Validation functions for stack heights in EOF containers.
"""
from typing import Callable, Dict

from ethereum_types.numeric import Uint

from ...vm.instructions import Ops, op_stack_items
from ..exceptions import InvalidEof
from . import Validator


def stack_validation_callf(validator: Validator) -> None:
    """
    Validate stack height for CALLF instruction.

    Parameters
    ----------
    validator : `Validator`
        The validator object.
    """
    eof_meta = validator.eof.metadata
    index = validator.current_index
    section_metadata = validator.sections[index]
    op_metadata = section_metadata[validator.current_pc]

    assert op_metadata.target_index is not None
    assert op_metadata.stack_height is not None
    assert validator.current_stack_height is not None

    target_section_type = eof_meta.type_section_contents[
        op_metadata.target_index
    ]
    target_inputs = target_section_type[0]
    target_outputs = target_section_type[1]
    target_max_height = int.from_bytes(target_section_type[2:], "big")

    # Stack Height Check
    if op_metadata.stack_height.min < target_inputs:
        raise InvalidEof("Invalid stack height")

    # Stack Overflow Check
    if op_metadata.stack_height.max > 1024 - target_max_height + target_inputs:
        raise InvalidEof("Stack overflow")

    # Update the stack height after instruction
    increment = target_outputs - target_inputs
    validator.current_stack_height.min += increment
    validator.current_stack_height.max += increment


def stack_validation_jumpf(validator: Validator) -> None:
    """
    Validate stack height for JUMPF instruction.

    Parameters
    ----------
    validator : `Validator`
        The validator object.
    """
    eof_meta = validator.eof.metadata
    index = validator.current_index
    section_metadata = validator.sections[index]
    op_metadata = section_metadata[validator.current_pc]

    assert op_metadata.target_index is not None
    assert op_metadata.stack_height is not None
    assert validator.current_stack_height is not None

    current_section_type = eof_meta.type_section_contents[index]
    target_section_type = eof_meta.type_section_contents[
        op_metadata.target_index
    ]

    current_outputs = current_section_type[1]
    target_inputs = target_section_type[0]
    target_outputs = target_section_type[1]
    target_max_height = int.from_bytes(target_section_type[2:], "big")

    # Stack Height Check
    if target_outputs != 0x80:
        expected_stack_height = (
            current_outputs + target_inputs - target_outputs
        )
        if op_metadata.stack_height.min != op_metadata.stack_height.max:
            raise InvalidEof("Invalid stack height")
        if op_metadata.stack_height.min != expected_stack_height:
            raise InvalidEof("Invalid stack height")
    else:
        if op_metadata.stack_height.min < target_inputs:
            raise InvalidEof("Invalid stack height")

    # Stack Overflow Check
    if op_metadata.stack_height.max > 1024 - target_max_height + target_inputs:
        raise InvalidEof("Stack overflow")

    # Update the stack height after instruction
    if target_outputs != 0x80:
        increment = target_outputs - target_inputs
        validator.current_stack_height.min += increment
        validator.current_stack_height.max += increment


def stack_validation_retf(validator: Validator) -> None:
    """
    Validate stack height for RETF instruction.

    Parameters
    ----------
    validator : `Validator`
        The validator object.
    """
    eof_meta = validator.eof.metadata
    index = validator.current_index
    section_metadata = validator.sections[index]
    op_metadata = section_metadata[validator.current_pc]

    assert op_metadata.stack_height is not None
    assert validator.current_stack_height is not None

    # Stack Height Check
    if op_metadata.stack_height.min != op_metadata.stack_height.max:
        raise InvalidEof("Invalid stack height")
    type_section = eof_meta.type_section_contents[index]
    type_section_outputs = type_section[1]
    if op_metadata.stack_height.min != type_section_outputs:
        raise InvalidEof("Invalid stack height")

    # Stack Overflow Check
    pass

    # Update the stack height after instruction
    opcode = op_metadata.opcode
    instruction_inputs = op_stack_items[opcode].inputs
    instruction_outputs = op_stack_items[opcode].outputs
    validator.current_stack_height.min += (
        instruction_outputs - instruction_inputs
    )
    validator.current_stack_height.max += (
        instruction_outputs - instruction_inputs
    )


def stack_validation_dupn(validator: Validator) -> None:
    """
    Validate stack height for DUPN instruction.

    Parameters
    ----------
    validator : `Validator`
        The validator object
    """
    eof_meta = validator.eof.metadata
    index = validator.current_index
    code = eof_meta.code_section_contents[index]

    assert validator.current_stack_height is not None

    # Stack Height Check
    immediate_data = code[validator.current_pc + Uint(1)]
    n = immediate_data + 1
    if validator.current_stack_height.min < n:
        raise InvalidEof("Invalid stack height for DUPN")

    # Stack Overflow Check
    pass

    # Update the stack height after instruction
    validator.current_stack_height.min += 1
    validator.current_stack_height.max += 1


def stack_validation_swapn(validator: Validator) -> None:
    """
    Validate stack height for SWAPN instruction.

    Parameters
    ----------
    validator : `Validator`
        The validator object.
    """
    eof_meta = validator.eof.metadata
    index = validator.current_index
    code = eof_meta.code_section_contents[index]

    assert validator.current_stack_height is not None

    # Stack Height Check
    immediate_data = code[validator.current_pc + Uint(1)]
    n = immediate_data + 1
    if validator.current_stack_height.min < n + 1:
        raise InvalidEof("Invalid stack height for SWAPN")

    # Stack Overflow Check
    pass

    # Update the stack height after instruction
    pass


def stack_validation_exchange(validator: Validator) -> None:
    """
    Validate stack height for EXCHANGE instruction.

    Parameters
    ----------
    validator : `Validator`
        The validator object.
    """
    index = validator.current_index
    code = validator.eof.metadata.code_section_contents[index]

    assert validator.current_stack_height is not None

    # Stack Height Check
    immediate_data = code[validator.current_pc + Uint(1)]
    n = (immediate_data >> 4) + 1
    m = (immediate_data & 0xF) + 1
    if validator.current_stack_height.min < n + m + 1:
        raise InvalidEof("Invalid stack height for EXCHANGE")

    # Stack Overflow Check
    pass

    # Update the stack height after instruction
    pass


def stack_validation_other_instructions(validator: Validator) -> None:
    """
    Validate stack height for other instructions.

    Parameters
    ----------
    validator : `Validator`
        The validator object.
    """
    index = validator.current_index
    section_metadata = validator.sections[index]
    op_metadata = section_metadata[validator.current_pc]
    opcode = op_metadata.opcode

    assert op_metadata.stack_height is not None
    assert validator.current_stack_height is not None

    # Stack Height Check
    instruction_inputs = op_stack_items[opcode].inputs
    if op_metadata.stack_height.min < instruction_inputs:
        raise InvalidEof("Invalid stack height")

    # Stack Overflow Check
    pass

    # Update the stack height after instruction
    instruction_inputs = op_stack_items[opcode].inputs
    instruction_outputs = op_stack_items[opcode].outputs
    validator.current_stack_height.min += (
        instruction_outputs - instruction_inputs
    )
    validator.current_stack_height.max += (
        instruction_outputs - instruction_inputs
    )


stack_validation: Dict[Ops, Callable] = {
    Ops.CALLF: stack_validation_callf,
    Ops.JUMPF: stack_validation_jumpf,
    Ops.RETF: stack_validation_retf,
    Ops.DUPN: stack_validation_dupn,
    Ops.SWAPN: stack_validation_swapn,
    Ops.EXCHANGE: stack_validation_exchange,
}


def get_stack_validation(op: Ops) -> Callable:
    """
    Fetch the relevant stack validation function for the
    given opcode.

    Parameters
    ----------
    op : `Ops`
        The opcode to validate.

    Returns
    -------
    validation_function : `Callable`
        The validation function for the given opcode.
    """
    if op in stack_validation:
        return stack_validation[op]
    else:
        return stack_validation_other_instructions
