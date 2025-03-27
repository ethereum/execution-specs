"""
Validation functions for opcodes in EOF containers.
"""


from typing import Callable, Dict, List

from ethereum_types.numeric import Uint

from ..exceptions import InvalidEof
from ..instructions import EOF1_TERMINATING_INSTRUCTIONS, Ops, map_int_to_op
from . import ContainerContext, EofVersion, InstructionMetadata, Validator


def validate_push(validator: Validator) -> None:
    """
    Validate PUSH instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    opcode = map_int_to_op(code[position], EofVersion.EOF1)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    push_data_size = opcode.value - Ops.PUSH1.value + 1
    if len(code) < counter + push_data_size:
        raise InvalidEof("Push data missing")
    counter += push_data_size

    # Successor instruction positions
    relative_offsets = [0]

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=opcode,
        pc_post_instruction=Uint(counter),
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_callf(validator: Validator) -> None:
    """
    Validate CALLF instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    eof_meta = validator.eof.metadata
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 2:
        raise InvalidEof("CALLF target code section index missing")
    target_index = Uint.from_be_bytes(
        code[counter : counter + 2],
    )
    counter += 2
    if target_index >= eof_meta.num_code_sections:
        raise InvalidEof("Invalid target code section index")
    reached_sections = validator.reached_code_sections[validator.current_index]
    reached_sections.add(target_index)

    target_type = eof_meta.type_section_contents[target_index]
    target_outputs = target_type[1]

    if target_outputs == 0x80:
        raise InvalidEof("CALLF into non-returning section")

    # Successor instruction positions
    relative_offsets = [0]

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.CALLF,
        pc_post_instruction=Uint(counter),
        relative_offsets=relative_offsets,
        target_index=target_index,
        container_index=None,
        stack_height=None,
    )


def validate_rjump(validator: Validator) -> None:
    """
    Validate RJUMP instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 2:
        raise InvalidEof("RJUMP target offset missing")
    relative_offset = int.from_bytes(
        code[counter : counter + 2], "big", signed=True
    )
    counter += 2

    # Successor instruction positions
    relative_offsets = [relative_offset]

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.RJUMP,
        pc_post_instruction=Uint(counter),
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_rjumpi(validator: Validator) -> None:
    """
    Validate RJIMPI instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 2:
        raise InvalidEof("RJUMPI relative offset missing")
    relative_offset = int.from_bytes(
        code[counter : counter + 2], "big", signed=True
    )
    counter += 2

    # Successor instruction positions
    relative_offsets = [0, relative_offset]

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.RJUMPI,
        pc_post_instruction=Uint(validator.current_pc),
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_rjumpv(validator: Validator) -> None:
    """
    Validate RJUMPV instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 1:
        raise InvalidEof("max_index missing for RJUMPV")
    max_index = code[counter]
    num_relative_indices = max_index + 1
    counter += 1

    # Successor instruction positions
    relative_offsets = [0]
    for _ in range(num_relative_indices):
        if len(code) < counter + 2:
            raise InvalidEof("Relative jump indices missing")
        relative_offset = int.from_bytes(
            code[counter : counter + 2],
            "big",
            signed=True,
        )
        counter += 2
        relative_offsets.append(relative_offset)

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.RJUMPV,
        pc_post_instruction=Uint(validator.current_pc),
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_jumpf(validator: Validator) -> None:
    """
    Validate JUMPF instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    index = validator.current_index
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    eof_meta = validator.eof.metadata
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 2:
        raise InvalidEof("JUMPF target code section index missing")
    target_index = Uint.from_be_bytes(
        code[counter : counter + 2],
    )
    counter += 2

    if target_index >= eof_meta.num_code_sections:
        raise InvalidEof("Invalid target code section index")

    current_section_type = eof_meta.type_section_contents[index]
    target_section_type = eof_meta.type_section_contents[target_index]

    current_outputs = current_section_type[1]
    target_outputs = target_section_type[1]

    if target_outputs != 0x80:
        if target_outputs > current_outputs:
            raise InvalidEof("Invalid stack height")
        validator.is_current_section_returning = True

    reached_sections = validator.reached_code_sections[validator.current_index]
    reached_sections.add(target_index)

    # Successor instruction positions
    relative_offsets: List[int] = []

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.JUMPF,
        pc_post_instruction=Uint(validator.current_pc),
        relative_offsets=relative_offsets,
        target_index=target_index,
        container_index=None,
        stack_height=None,
    )


def validate_dataloadn(validator: Validator) -> None:
    """
    Validate DATALOADN instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    eof_meta = validator.eof.metadata
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 2:
        raise InvalidEof("DATALOADN offset missing")
    offset = Uint.from_be_bytes(code[position + Uint(1) : position + Uint(3)])
    if offset + Uint(32) > eof_meta.data_size:
        raise InvalidEof("Invalid DATALOADN offset")
    counter += 2

    # Successor instruction positions
    relative_offsets = [0]

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.DATALOADN,
        pc_post_instruction=Uint(validator.current_pc),
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_dupn(validator: Validator) -> None:
    """
    Validate DUPN instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 1:
        raise InvalidEof("DUPN index missing")
    counter += 1

    # Successor instruction positions
    relative_offsets = [0]

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.DUPN,
        pc_post_instruction=Uint(validator.current_pc),
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_swapn(validator: Validator) -> None:
    """
    Validate SWAPN instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 1:
        raise InvalidEof("SWAPN index missing")
    counter += 1

    # Successor instruction positions
    relative_offsets = [0]

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.SWAPN,
        pc_post_instruction=Uint(validator.current_pc),
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_exchange(validator: Validator) -> None:
    """
    Validate EXCHANGE instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 1:
        raise InvalidEof("EXCHANGE index missing")
    counter += 1

    # Successor instruction positions
    relative_offsets = [0]

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.EXCHANGE,
        pc_post_instruction=Uint(validator.current_pc),
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_eofcreate(validator: Validator) -> None:
    """
    Validate EOFCREATE instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 1:
        raise InvalidEof("EOFCREATE index missing")
    container_index = Uint.from_be_bytes(code[counter : counter + 1])
    if container_index >= validator.eof.metadata.num_container_sections:
        raise InvalidEof("Invalid EOFCREATE index")
    counter += 1

    # Successor instruction positions
    relative_offsets = [0]

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    validator.referenced_subcontainers[Ops.EOFCREATE].append(container_index)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.EOFCREATE,
        pc_post_instruction=Uint(validator.current_pc),
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=container_index,
        stack_height=None,
    )


def validate_returncontract(validator: Validator) -> None:
    """
    Validate RETURNCONTRACT instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    context = validator.eof.metadata.context
    if context in (
        ContainerContext.RETURNCONTRACT_TARGET,
        ContainerContext.RUNTIME,
    ):
        raise InvalidEof(
            "RETURNCONTRACT instruction in RUNTIME "
            "container/RETURNCONTRACT target"
        )
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Immediate Data Check
    if len(code) < counter + 1:
        raise InvalidEof("RETURNCONTRACT index missing")
    container_index = Uint.from_be_bytes(code[counter : counter + 1])
    if container_index >= validator.eof.metadata.num_container_sections:
        raise InvalidEof("Invalid RETURNCONTRACT index")
    counter += 1

    # Successor instruction positions
    relative_offsets: List[int] = []

    # Update Instruction Metadata
    validator.has_return_contract = True
    validator.current_pc = Uint(counter)
    validator.referenced_subcontainers[Ops.RETURNCONTRACT].append(
        container_index
    )
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.RETURNCONTRACT,
        pc_post_instruction=validator.current_pc,
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=container_index,
        stack_height=None,
    )


def validate_stop(validator: Validator) -> None:
    """
    Validate STOP instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    context = validator.eof.metadata.context
    if context in (ContainerContext.INIT, ContainerContext.CREATE_TX_DATA):
        raise InvalidEof("STOP instruction in EOFCREATE target/ initcode")

    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Successor instruction positions
    relative_offsets: List[int] = []

    # Update Instruction Metadata
    validator.has_stop = True
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.STOP,
        pc_post_instruction=validator.current_pc,
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_return(validator: Validator) -> None:
    """
    Validate RETURN instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    context = validator.eof.metadata.context
    if context in (ContainerContext.INIT, ContainerContext.CREATE_TX_DATA):
        raise InvalidEof("RETURN instruction in EOFCREATE target/ initcode")
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})

    # Successor instruction positions
    relative_offsets: List[int] = []

    # Update Instruction Metadata
    validator.has_return = True
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=Ops.RETURN,
        pc_post_instruction=validator.current_pc,
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_retf(validator: Validator) -> None:
    """
    Validate the RETF instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})
    opcode = map_int_to_op(code[position], EofVersion.EOF1)
    index = validator.current_index
    eof_meta = validator.eof.metadata

    section_type = eof_meta.type_section_contents[index]
    outputs = section_type[1]
    if outputs == 0x80:
        raise InvalidEof("RETF in non-returning section")

    validator.is_current_section_returning = True

    # Successor instruction positions
    relative_offsets: List[int] = []

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=opcode,
        pc_post_instruction=validator.current_pc,
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_other_terminating_instructions(validator: Validator) -> None:
    """
    Validate other terminating instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})
    opcode = map_int_to_op(code[position], EofVersion.EOF1)

    # Successor instruction positions
    relative_offsets: List[int] = []

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=opcode,
        pc_post_instruction=validator.current_pc,
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


def validate_other_instructions(validator: Validator) -> None:
    """
    Validate other instructions.

    Parameters
    ----------
    validator : `Validator`
        The current validator instance.
    """
    code = validator.current_code
    position = Uint(validator.current_pc)
    counter = int(validator.current_pc) + 1
    current_metadata = validator.sections.get(validator.current_index, {})
    opcode = map_int_to_op(code[position], EofVersion.EOF1)

    # Successor instruction positions
    relative_offsets = [0]

    # Update Instruction Metadata
    validator.current_pc = Uint(counter)
    current_metadata[position] = InstructionMetadata(
        opcode=opcode,
        pc_post_instruction=validator.current_pc,
        relative_offsets=relative_offsets,
        target_index=None,
        container_index=None,
        stack_height=None,
    )


op_validation: Dict[Ops, Callable] = {
    Ops.PUSH1: validate_push,
    Ops.PUSH2: validate_push,
    Ops.PUSH3: validate_push,
    Ops.PUSH4: validate_push,
    Ops.PUSH5: validate_push,
    Ops.PUSH6: validate_push,
    Ops.PUSH7: validate_push,
    Ops.PUSH8: validate_push,
    Ops.PUSH9: validate_push,
    Ops.PUSH10: validate_push,
    Ops.PUSH11: validate_push,
    Ops.PUSH12: validate_push,
    Ops.PUSH13: validate_push,
    Ops.PUSH14: validate_push,
    Ops.PUSH15: validate_push,
    Ops.PUSH16: validate_push,
    Ops.PUSH17: validate_push,
    Ops.PUSH18: validate_push,
    Ops.PUSH19: validate_push,
    Ops.PUSH20: validate_push,
    Ops.PUSH21: validate_push,
    Ops.PUSH22: validate_push,
    Ops.PUSH23: validate_push,
    Ops.PUSH24: validate_push,
    Ops.PUSH25: validate_push,
    Ops.PUSH26: validate_push,
    Ops.PUSH27: validate_push,
    Ops.PUSH28: validate_push,
    Ops.PUSH29: validate_push,
    Ops.PUSH30: validate_push,
    Ops.PUSH31: validate_push,
    Ops.PUSH32: validate_push,
    Ops.CALLF: validate_callf,
    Ops.RJUMP: validate_rjump,
    Ops.RJUMPI: validate_rjumpi,
    Ops.RJUMPV: validate_rjumpv,
    Ops.JUMPF: validate_jumpf,
    Ops.DATALOADN: validate_dataloadn,
    Ops.DUPN: validate_dupn,
    Ops.SWAPN: validate_swapn,
    Ops.EXCHANGE: validate_exchange,
    Ops.EOFCREATE: validate_eofcreate,
    Ops.RETURNCONTRACT: validate_returncontract,
    Ops.STOP: validate_stop,
    Ops.RETURN: validate_return,
    Ops.RETF: validate_retf,
}


def get_op_validation(op: Ops) -> Callable:
    """
    Fetch the relevant validation function for the
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
    if op in op_validation:
        return op_validation[op]
    elif op in EOF1_TERMINATING_INSTRUCTIONS:
        return validate_other_terminating_instructions
    else:
        return validate_other_instructions
