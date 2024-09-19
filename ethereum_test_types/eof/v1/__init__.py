"""
EVM Object Format Version 1 Library to generate bytecode for testing purposes
"""

from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple

from pydantic import Field, GetCoreSchemaHandler
from pydantic_core.core_schema import (
    PlainValidatorFunctionSchema,
    no_info_plain_validator_function,
    to_string_ser_schema,
)

from ethereum_test_base_types import Bytes
from ethereum_test_base_types.conversions import BytesConvertible
from ethereum_test_base_types.pydantic import CopyValidateModel
from ethereum_test_exceptions.exceptions import EOFExceptionInstanceOrList
from ethereum_test_vm import Bytecode
from ethereum_test_vm import Opcodes as Op

from ..constants import EOF_HEADER_TERMINATOR, EOF_MAGIC
from .constants import (
    HEADER_SECTION_COUNT_BYTE_LENGTH,
    HEADER_SECTION_KIND_BYTE_LENGTH,
    HEADER_SECTION_SIZE_BYTE_LENGTH,
    NON_RETURNING_SECTION,
    TYPES_INPUTS_BYTE_LENGTH,
    TYPES_OUTPUTS_BYTE_LENGTH,
    TYPES_STACK_BYTE_LENGTH,
    VERSION_NUMBER_BYTES,
)

VERSION_MAX_SECTION_KIND = 3


class SectionKind(IntEnum):
    """
    Enum class of V1 valid section kind values
    """

    TYPE = 1
    CODE = 2
    CONTAINER = 3
    DATA = 4

    def __str__(self) -> str:
        """
        Returns the string representation of the section kind
        """
        return self.name


class ContainerKind(Enum):
    """
    Enum class of V1 valid container kind values.
    """

    RUNTIME = auto()
    INITCODE = auto()

    @staticmethod
    def __get_pydantic_core_schema__(
        source_type: Any, handler: GetCoreSchemaHandler
    ) -> PlainValidatorFunctionSchema:
        """
        Calls the class constructor without info and appends the serialization schema.
        """
        return no_info_plain_validator_function(
            source_type.from_str,
            serialization=to_string_ser_schema(),
        )

    @staticmethod
    def from_str(value: "str | ContainerKind | None") -> "ContainerKind | None":
        """
        Returns the ContainerKind enum value from a string.
        """
        if value is None:
            return None
        if isinstance(value, ContainerKind):
            return value
        return ContainerKind[value.upper()]

    def __str__(self) -> str:
        """
        Returns the string representation of the container kind
        """
        return self.name


class AutoSection(Enum):
    """
    Enum class for auto section generation approach
    """

    AUTO = 1
    ONLY_HEADER = 2
    ONLY_BODY = 3
    NONE = 4

    def any(self) -> bool:
        """
        Returns True if the enum is not NONE
        """
        return self != AutoSection.NONE

    def header(self) -> bool:
        """
        Returns True if the enum is not ONLY_BODY
        """
        return self != AutoSection.ONLY_BODY and self != AutoSection.NONE

    def body(self) -> bool:
        """
        Returns True if the enum is not ONLY_HEADER
        """
        return self != AutoSection.ONLY_HEADER and self != AutoSection.NONE


SUPPORT_MULTI_SECTION_HEADER = [SectionKind.CODE, SectionKind.CONTAINER]


class Section(CopyValidateModel):
    """
    Class that represents a section in an EOF V1 container.
    """

    data: Bytes = Bytes(b"")
    """
    Data to be contained by this section.
    Can be SupportsBytes, another EOF container or any other abstract data.
    """
    custom_size: int = 0
    """
    Custom size value to be used in the header.
    If unset, the header is built with length of the data.
    """
    kind: SectionKind | int
    """
    Kind of section that is represented by this object.
    Can be any `int` outside of the values defined by `SectionKind`
    for testing purposes.
    """
    force_type_listing: bool = False
    """
    Forces this section to appear in the TYPE section at the beginning of the
    container.
    """
    code_inputs: int = 0
    """
    Data stack items consumed by this code section (function)
    """
    code_outputs: int = NON_RETURNING_SECTION
    """
    Data stack items produced by or expected at the end of this code section
    (function)
    """
    max_stack_height: int = 0
    """
    Maximum height data stack reaches during execution of code section.
    """
    auto_max_stack_height: bool = False
    """
    Whether to automatically compute the best suggestion for the
    max_stack_height value for this code section.
    """
    auto_code_inputs_outputs: bool = False
    """
    Whether to automatically compute the best suggestion for the code_inputs,
    code_outputs values for this code section.
    """
    skip_header_listing: bool = False
    """
    Skip section from listing in the header
    """
    skip_body_listing: bool = False
    """
    Skip section from listing in the body
    """
    skip_types_body_listing: bool = False
    """
    Skip section from listing in the types body (input, output, stack) bytes
    """
    skip_types_header_listing: bool = False
    """
    Skip section from listing in the types header (not calculating input, output, stack size)
    """

    @cached_property
    def header(self) -> bytes:
        """
        Get formatted header for this section according to its contents.
        """
        size = self.custom_size if "custom_size" in self.model_fields_set else len(self.data)
        if self.kind == SectionKind.CODE:
            raise Exception("Need container-wide view of code sections to generate header")
        return self.kind.to_bytes(
            HEADER_SECTION_KIND_BYTE_LENGTH, byteorder="big"
        ) + size.to_bytes(HEADER_SECTION_SIZE_BYTE_LENGTH, byteorder="big")

    @cached_property
    def type_definition(self) -> bytes:
        """
        Returns a serialized type section entry for this section.
        """
        if self.kind != SectionKind.CODE and not self.force_type_listing:
            return bytes()

        code_inputs, code_outputs, max_stack_height = (
            self.code_inputs,
            self.code_outputs,
            self.max_stack_height,
        )
        if self.auto_max_stack_height or self.auto_code_inputs_outputs:
            (
                auto_code_inputs,
                auto_code_outputs,
                auto_max_height,
            ) = compute_code_stack_values(self.data)
            if self.auto_max_stack_height:
                max_stack_height = auto_max_height
            if self.auto_code_inputs_outputs:
                code_inputs, code_outputs = (
                    auto_code_inputs,
                    auto_code_outputs,
                )

        return (
            code_inputs.to_bytes(length=TYPES_INPUTS_BYTE_LENGTH, byteorder="big")
            + code_outputs.to_bytes(length=TYPES_OUTPUTS_BYTE_LENGTH, byteorder="big")
            + max_stack_height.to_bytes(length=TYPES_STACK_BYTE_LENGTH, byteorder="big")
        )

    def with_max_stack_height(self, max_stack_height) -> "Section":
        """
        Creates a copy of the section with `max_stack_height` set to the
        specified value.
        """
        return self.copy(max_stack_height=max_stack_height)

    def with_auto_max_stack_height(self) -> "Section":
        """
        Creates a copy of the section with `auto_max_stack_height` set to True.
        """
        return self.copy(auto_max_stack_height=True)

    def with_auto_code_inputs_outputs(self) -> "Section":
        """
        Creates a copy of the section with `auto_code_inputs_outputs` set to
        True.
        """
        return self.copy(auto_code_inputs_outputs=True)

    @staticmethod
    def list_header(sections: List["Section"]) -> bytes:
        """
        Creates the single code header for all code sections contained in
        the list.
        """
        # Allow 'types section' to use skip_header_listing flag
        if sections[0].skip_header_listing:
            return b""

        if sections[0].kind not in SUPPORT_MULTI_SECTION_HEADER:
            return b"".join(s.header for s in sections)

        h = sections[0].kind.to_bytes(HEADER_SECTION_KIND_BYTE_LENGTH, "big")

        # Count only those sections that are not marked to be skipped for header calculation
        header_registered_sections = 0
        for cs in sections:
            if not cs.skip_header_listing:
                header_registered_sections += 1

        h += header_registered_sections.to_bytes(HEADER_SECTION_COUNT_BYTE_LENGTH, "big")
        for cs in sections:
            # If section is marked to skip the header calculation, don't make header for it
            if cs.skip_header_listing:
                continue
            size = cs.custom_size if "custom_size" in cs.model_fields_set else len(cs.data)
            h += size.to_bytes(HEADER_SECTION_SIZE_BYTE_LENGTH, "big")

        return h

    @classmethod
    def Code(  # noqa: N802
        cls, code: BytesConvertible | Bytecode = Bytecode(), **kwargs
    ) -> "Section":
        """
        Creates a new code section with the specified code.
        """
        kwargs.pop("kind", None)
        if "max_stack_height" not in kwargs and isinstance(code, Bytecode):
            kwargs["max_stack_height"] = code.max_stack_height
        return cls(kind=SectionKind.CODE, data=code, **kwargs)

    @classmethod
    def Container(  # noqa: N802
        cls, container: "Container" | BytesConvertible, **kwargs
    ) -> "Section":
        """
        Creates a new container section with the specified container.
        """
        kwargs.pop("kind", None)
        return cls(kind=SectionKind.CONTAINER, data=container, **kwargs)

    @classmethod
    def Data(cls, data: BytesConvertible = b"", **kwargs) -> "Section":  # noqa: N802
        """
        Creates a new data section with the specified data.
        """
        kwargs.pop("kind", None)
        return cls(kind=SectionKind.DATA, data=data, **kwargs)


class Container(CopyValidateModel):
    """
    Class that represents an EOF V1 container.
    """

    name: Optional[str] = None
    """
    Name of the container
    """
    sections: List[Section] = Field(default_factory=list)
    """
    List of sections in the container
    """
    magic: Bytes = Bytes(EOF_MAGIC)
    """
    Custom magic value used to override the mandatory EOF value for testing
    purposes.
    """
    version: Bytes = Bytes(VERSION_NUMBER_BYTES)
    """
    Custom version value used to override the mandatory EOF V1 value
    for testing purposes.
    """
    header_terminator: Bytes = Bytes(EOF_HEADER_TERMINATOR)
    """
    Bytes used to terminate the header.
    """
    extra: Bytes = Bytes(b"")
    """
    Extra data to be appended at the end of the container, which will
    not be considered part of any of the sections, for testing purposes.
    """
    auto_type_section: AutoSection = AutoSection.AUTO
    """
    Automatically generate a `TYPE` section based on the
    included `CODE` kind sections.
    """
    auto_data_section: bool = True
    """
    Automatically generate a `DATA` section.
    """
    auto_sort_sections: AutoSection = AutoSection.AUTO
    """
    Automatically sort sections for the header and body:
    Headers: type section first, all code sections, container sections, last
                data section(s)
    Body: type section first, all code sections, data section(s), last
                container sections
    """
    skip_join_concurrent_sections_in_header: bool = False
    """
    Skip joining concurrent sections in the header (code and container)
    """
    validity_error: EOFExceptionInstanceOrList | str | None = None
    """
    Optional error expected for the container.

    TODO: Remove str
    """
    kind: ContainerKind = ContainerKind.RUNTIME
    """
    Kind type of the container.
    """
    raw_bytes: Optional[Bytes] = None
    """
    Optional raw bytes that represent the container.
    Used to have a cohesive type among all test cases, even those that do not
    resemble a valid EOF V1 container.
    """
    expected_bytecode: Optional[Bytes] = None
    """
    Optional raw bytes of the expected constructed bytecode.
    This allows confirming that raw EOF and Container() representations are identical.
    """

    @cached_property
    def bytecode(self) -> bytes:
        """
        Converts the EOF V1 Container into bytecode.
        """
        if self.raw_bytes is not None:
            assert len(self.sections) == 0
            return self.raw_bytes

        c = self.magic + self.version

        # Prepare auto-generated sections
        sections = self.sections

        # Add type section if needed
        if self.auto_type_section.any() and count_sections(sections, SectionKind.TYPE) == 0:
            # Calculate skipping flags
            types_header_size = 0
            type_section_data = b""
            for s in sections:
                types_header_size += (
                    len(s.type_definition) if not s.skip_types_header_listing else 0
                )
                type_section_data += s.type_definition if not s.skip_types_body_listing else b""

            sections = [
                Section(
                    kind=SectionKind.TYPE, data=type_section_data, custom_size=types_header_size
                )
            ] + sections

        # Add data section if needed
        if self.auto_data_section and count_sections(sections, SectionKind.DATA) == 0:
            sections = sections + [Section(kind=SectionKind.DATA, data="0x")]

        header_sections = [
            s
            for s in sections
            if s.kind != SectionKind.TYPE or self.auto_type_section != AutoSection.ONLY_BODY
        ]
        if self.auto_sort_sections.header():
            header_sections.sort(key=lambda x: x.kind)

        # Add headers
        if header_sections:
            # Join headers of the same kind in a list of lists, only if they are next to each other
            concurrent_sections: List[List[Section]] = [[header_sections[0]]]
            for s in header_sections[1:]:
                if (
                    s.kind == concurrent_sections[-1][-1].kind
                    and not self.skip_join_concurrent_sections_in_header
                ):
                    concurrent_sections[-1].append(s)
                else:
                    concurrent_sections.append([s])
            c += b"".join(Section.list_header(cs) for cs in concurrent_sections)

        # Add header terminator
        c += self.header_terminator

        body_sections = sections[:]
        if self.auto_sort_sections.body():
            # Sort sections for the body
            body_sections.sort(key=lambda x: x.kind)

        # Add section bodies
        for s in body_sections:
            if s.kind == SectionKind.TYPE and self.auto_type_section == AutoSection.ONLY_HEADER:
                continue
            if s.data and not s.skip_body_listing:
                c += s.data

        # Add extra (garbage)
        c += self.extra

        # Check if the constructed bytecode matches the expected one
        if self.expected_bytecode is not None:
            assert c == self.expected_bytecode

        return c

    @classmethod
    def Code(cls, code: BytesConvertible = Bytecode(), **kwargs) -> "Container":  # noqa: N802
        """
        Creates simple container with a single code section.
        """
        kwargs.pop("kind", None)
        return cls(sections=[Section.Code(code=code, **kwargs)])

    @classmethod
    def Init(  # noqa: N802
        cls,
        deploy_container: "Container",
        initcode_prefix: Bytecode = Bytecode(),
    ) -> "Container":
        """
        Creates simple init container that deploys the specified container.
        """
        return cls(
            sections=[
                Section.Code(
                    code=initcode_prefix + Op.RETURNCONTRACT[0](0, 0),
                ),
                Section.Container(
                    container=deploy_container,
                ),
            ],
        )

    def __bytes__(self) -> bytes:
        """
        Returns the bytecode of the container.
        """
        return self.bytecode

    def __len__(self) -> int:
        """
        Returns the length of the container bytecode.
        """
        return len(self.bytecode)

    def __str__(self) -> str:
        """
        Returns the name of the container if available, otherwise the bytecode of the container
        as a string.
        """
        if self.name:
            return self.name
        return str(self.bytecode)


@dataclass(kw_only=True)
class Initcode(Bytecode):
    """
    Helper class used to generate initcode for the specified deployment code,
    using EOF V1 container as init code.
    """

    name: str = "EOF V1 Initcode"
    """
    Name used to identify the initcode.
    """
    deploy_container: Container
    """
    Container to be deployed.
    """

    @cached_property
    def init_container(self) -> Container:
        """
        Generate a container that will be used as the initcode.
        """
        return Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCONTRACT[0](0, 0),
                    max_stack_height=2,
                ),
                Section.Container(
                    container=self.deploy_container,
                ),
            ],
        )

    @cached_property
    def bytecode(self) -> bytes:
        """
        Generate an EOF container performs `EOFCREATE` with the specified code.
        """
        initcode = Container(
            sections=[
                Section.Code(
                    # TODO: Pass calldata
                    code=Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP(),
                    max_stack_height=4,
                ),
                Section.Container(
                    container=self.init_container,
                ),
            ]
        )

        return bytes(initcode)


def count_sections(sections: List[Section], kind: SectionKind | int) -> int:
    """
    Counts sections from a list that match a specific kind
    """
    return len([s for s in sections if s.kind == kind])


OPCODE_MAP: Dict[int, Op] = {x.int(): x for x in Op}


def compute_code_stack_values(code: bytes) -> Tuple[int, int, int]:
    """
    Computes the stack values for the given bytecode.

    TODO: THIS DOES NOT WORK WHEN THE RJUMP* JUMPS BACKWARDS (and many other
    things).
    """
    i = 0
    stack_height = 0
    min_stack_height = 0
    max_stack_height = 0

    # compute type annotation
    while i < len(code):
        op = OPCODE_MAP.get(code[i])
        if op is None:
            return (0, 0, 0)
        elif op == Op.RJUMPV:
            i += 1
            if i < len(code):
                count = code[i]
                i += count * 2
        else:
            i += 1 + op.data_portion_length

        stack_height -= op.popped_stack_items
        min_stack_height = min(stack_height, min_stack_height)
        stack_height += op.pushed_stack_items
        max_stack_height = max(stack_height, max_stack_height)
    if stack_height < 0:
        stack_height = 0
    return (abs(min_stack_height), stack_height, max_stack_height)
