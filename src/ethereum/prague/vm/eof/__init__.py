"""
Ethereum Object Format (EOF)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the Ethereum Object Format (EOF) specification.
"""

import enum
from dataclasses import dataclass
from typing import Dict, List, Optional

from ethereum.base_types import Bytes, Uint

from ..exceptions import InvalidEof

EOF_MAGIC = b"\xEF\x00"
EOF_MAGIC_LENGTH = len(EOF_MAGIC)


class EofVersion(enum.Enum):
    """
    Enumeration of the different kinds of EOF containers.
    Legacy code is assigned zero.
    """

    LEGACY = 0
    EOF1 = 1


@dataclass
class EofMetadata:
    """
    Dataclass to hold the metadata information of the
    EOF container.
    """

    type_size: Uint
    num_code_sections: Uint
    code_sizes: List[Uint]
    num_container_sections: Uint
    container_sizes: List[Uint]
    data_size: Uint
    body_start_index: Uint
    type_section_contents: List[bytes]
    code_section_contents: List[bytes]
    container_section_contents: List[bytes]
    data_section_contents: bytes


@dataclass
class Eof:
    """
    Dataclass to hold the EOF container information.
    """

    version: EofVersion
    container: Bytes
    metadata: EofMetadata
    is_deploy_container: bool
    is_init_container: bool


@dataclass
class ReturnStackItem:
    """
    Stack item for the return stack.
    """

    code_section_index: Uint
    offset: Uint


@dataclass
class OperandStackHeight:
    """
    Stack height bounds of an instruction.
    """

    min: int
    max: int


@dataclass
class InstructionMetadata:
    """
    Metadata of an instruction in the code section.
    """

    from ..instructions import Ops

    opcode: Ops
    pc_post_instruction: Uint
    relative_offsets: List[int]
    target_index: Optional[Uint]
    container_index: Optional[Uint]
    stack_height: Optional[OperandStackHeight]


SectionMetadata = Dict[Uint, InstructionMetadata]


@dataclass
class Validator:
    """
    Validator for the Ethereum Object Format (EOF) container.
    """

    from ..instructions import Ops

    eof: Eof
    sections: Dict[Uint, SectionMetadata]
    current_index: Uint
    current_code: bytes
    current_pc: Uint
    has_return_contract: bool
    has_stop: bool
    has_return: bool
    referenced_subcontainers: Dict[Ops, List[Uint]]
    current_stack_height: Optional[OperandStackHeight]


def get_eof_version(code: bytes) -> EofVersion:
    """
    Get the Eof container's version.

    Parameters
    ----------
    code : bytes
        The code to check.

    Returns
    -------
    Eof
        Eof Version of the container.
    """
    if not code.startswith(EOF_MAGIC):
        return EofVersion.LEGACY

    if code[EOF_MAGIC_LENGTH] == 1:
        return EofVersion.EOF1
    else:
        raise InvalidEof("Invalid EOF version")
