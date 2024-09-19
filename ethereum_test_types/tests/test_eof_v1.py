"""
Test suite for `code.eof.v1` module.
"""

from typing import List, Tuple

import pytest

from ethereum_test_base_types import to_json
from ethereum_test_base_types.pydantic import CopyValidateModel
from ethereum_test_vm import Opcodes as Op

from ..eof.v1 import AutoSection, Container, Section, SectionKind

test_cases: List[Tuple[str, Container, str]] = [
    (
        "No sections",
        Container(
            auto_data_section=False,
            auto_type_section=AutoSection.NONE,
            sections=[],
        ),
        "ef0001 00",
    ),
    (
        "Single code section",
        Container(
            sections=[
                Section.Code("0x00"),
            ],
        ),
        "ef0001 01 0004 02 0001 0001 04 0000 00 00800000 00",
    ),
    (
        "Single code section, single container section",
        Container(
            sections=[
                Section.Code("0x0A"),
                Section.Container("0x0B"),
            ],
        ),
        "ef0001 01 0004 02 0001 0001 03 0001 0001 04 0000 00 00800000 0A 0B",
    ),
    (
        "Single code section, single container section, single data",
        Container(
            sections=[
                Section.Code("0x0A"),
                Section.Container("0x0B"),
                Section.Data("0x0C"),
            ],
        ),
        "ef0001 01 0004 02 0001 0001 03 0001 0001 04 0001 00 00800000 0A 0B 0C",
    ),
    (
        "Single code section, single container section, single data 2",
        Container(
            sections=[
                Section.Code("0x0A"),
                Section.Data("0x0C"),
                Section.Container("0x0B"),
            ],
        ),
        "ef0001 01 0004 02 0001 0001 03 0001 0001 04 0001 00 00800000 0A 0B 0C",
    ),
    (
        "Single code section, multiple container section, single data",
        Container(
            sections=[
                Section.Code("0x0A"),
                Section.Container("0x0B"),
                Section.Data("0x0C"),
                Section.Container("0x0D"),
            ],
        ),
        "ef0001 01 0004 02 0001 0001 03 0002 0001 0001 04 0001 00 00800000 0A 0B 0D 0C",
    ),
    (
        "Single code section, multiple container sections",
        Container(
            sections=[
                Section.Code("0x00"),
                Section.Container("0x0001"),
                Section.Container("0x00"),
            ],
        ),
        "ef0001 01 0004 02 0001 0001 03 0002 0002 0001 04 0000 00 00800000 00 0001 00",
    ),
    (
        "No code section",
        Container(
            sections=[Section.Data("0x00")],
        ),
        "ef0001 01 0000 04 0001 00 00",
    ),
    (
        "Single data section",
        Container(
            auto_type_section=AutoSection.NONE,
            sections=[
                Section.Data("0x00"),
            ],
        ),
        "ef0001 04 0001 00 00",
    ),
    (
        "Custom invalid section",
        Container(
            auto_data_section=False,
            auto_type_section=AutoSection.NONE,
            sections=[
                Section(
                    kind=0xFE,
                    data="0x00",
                ),
            ],
        ),
        "ef0001 fe 0001 00 00",
    ),
    (
        "Multiple sections",
        Container(
            sections=[
                Section.Code("0x0e"),
                Section.Data("0x0f"),
            ],
        ),
        "ef0001 01 0004 02 0001 0001 04 0001 00 00800000 0e 0f",
    ),
    (
        "Multiple type sections",
        Container(
            sections=[
                Section(
                    kind=SectionKind.TYPE,
                    data="0x00000000",
                ),
                Section(
                    kind=SectionKind.TYPE,
                    data="0x00000000",
                ),
                Section.Code("0x00"),
            ],
            auto_type_section=AutoSection.NONE,
        ),
        "ef0001 01 0004 01 0004 02 0001 0001 04 0000 00 00000000 00000000 00",
    ),
    (
        "Invalid Magic",
        Container(
            magic=b"\xEF\xFE",
            sections=[
                Section.Code("0x00"),
            ],
        ),
        "effe01 01 0004 02 0001 0001 04 0000 00 00800000 00",
    ),
    (
        "Invalid Version",
        Container(
            version=b"\x02",
            sections=[
                Section.Code("0x00"),
            ],
        ),
        "ef0002 01 0004 02 0001 0001 04 0000 00 00800000 00",
    ),
    (
        "Section Invalid size Version",
        Container(
            sections=[
                Section.Code(
                    "0x00",
                    custom_size=0xFFFF,
                ),
            ],
        ),
        "ef0001 01 0004 02 0001 ffff 04 0000 00 00800000 00",
    ),
    (
        "Nested EOF",
        Container(
            sections=[
                Section.Code("0x00"),
                Section(
                    kind=SectionKind.CONTAINER,
                    data=Container(
                        sections=[Section.Code("0x01")],
                    ),
                ),
            ],
        ),
        "ef0001 01 0004 02 0001 0001 03 0001 0014 04 0000 00 00800000 00"
        "ef0001 01 0004 02 0001 0001 04 0000 00 00800000 01",
    ),
    (
        "Nested EOF in Data",
        Container(
            sections=[
                Section.Code("0x00"),
                Section.Data(
                    data=Container(
                        sections=[Section.Code("0x01")],
                    ),
                ),
            ],
        ),
        "ef0001 01 0004 02 0001 0001 04 0014 00 00800000 00"
        "ef0001 01 0004 02 0001 0001 04 0000 00 00800000 01",
    ),
    (
        "Incomplete code section",
        Container(
            sections=[
                Section.Code(
                    code=b"",
                    custom_size=0x02,
                ),
            ],
        ),
        "ef0001 01 0004 02 0001 0002 04 0000 00 00800000",
    ),
    (
        "Trailing bytes after code section",
        Container(
            sections=[
                Section.Code("0x600000"),
            ],
            extra=bytes.fromhex("deadbeef"),
        ),
        "ef0001 01 0004 02 0001 0003 04 0000 00 00800000 600000 deadbeef",
    ),
    (
        "Multiple code sections",
        Container(
            sections=[
                Section.Code("0x600000"),
                Section.Code("0x600000"),
            ],
        ),
        """
            ef0001 01 0008 02 0002 0003 0003 04 0000 00
            00800000 00800000
            600000
            600000
            """,
    ),
    (
        "No section terminator",
        Container(
            sections=[
                Section.Code("0x600000"),
            ],
            header_terminator=bytes(),
        ),
        "ef0001 01 0004 02 0001 0003 04 0000 00800000 600000",
    ),
    (
        "No auto type section",
        Container(
            auto_type_section=AutoSection.NONE,
            sections=[
                Section.Code("0x00"),
            ],
        ),
        "ef0001 02 0001 0001 04 0000 00 00",
    ),
    (
        "Data section in types",
        Container(
            sections=[
                Section.Code("0x00"),
                Section.Data(
                    data="0x00",
                    force_type_listing=True,
                ),
            ],
        ),
        """
            ef0001 01 0008 02 0001 0001 04 0001 00
            00800000 00800000
            00 00
            """,
    ),
    (
        "Code section inputs",
        Container(
            sections=[
                Section.Code(
                    "0x00",
                    code_inputs=1,
                ),
            ],
        ),
        """
            ef0001 01 0004 02 0001 0001 04 0000 00
            01800000
            00
            """,
    ),
    (
        "Code section inputs 2",
        Container(
            sections=[
                Section.Code(
                    "0x00",
                    code_inputs=0xFF,
                ),
            ],
        ),
        """
            ef0001 01 0004 02 0001 0001 04 0000 00
            ff800000
            00
            """,
    ),
    (
        "Code section outputs",
        Container(
            sections=[
                Section.Code(
                    "0x00",
                    code_outputs=1,
                ),
            ],
        ),
        """
            ef0001 01 0004 02 0001 0001 04 0000 00
            00010000
            00
            """,
    ),
    (
        "Code section outputs 2",
        Container(
            sections=[
                Section.Code(
                    "0x00",
                    code_outputs=0xFF,
                ),
            ],
        ),
        """
            ef0001 01 0004 02 0001 0001 04 0000 00
            00ff0000
            00
            """,
    ),
    (
        "Code section max stack height",
        Container(
            sections=[
                Section.Code(
                    "0x00",
                    max_stack_height=0x0201,
                ),
            ],
        ),
        """
            ef0001 01 0004 02 0001 0001 04 0000 00
            00800201
            00
            """,
    ),
    (
        "Code section max stack height 2",
        Container(
            sections=[
                Section.Code(
                    "0x00",
                    max_stack_height=0xFFFF,
                ),
            ],
        ),
        """
            ef0001 01 0004 02 0001 0001 04 0000 00
            0080FFFF
            00
            """,
    ),
    (
        "Code section max stack height 3",
        Container(
            sections=[
                Section.Code(
                    "0x00",
                    max_stack_height=0xFFFF,
                ),
                Section.Code("0x00"),
            ],
        ),
        """
            ef0001 01 0008 02 0002 0001 0001 04 0000 00
            0080FFFF 00800000
            00
            00
            """,
    ),
    (
        "Custom type section",
        Container(
            sections=[
                Section(
                    kind=SectionKind.TYPE,
                    data="0x00",
                ),
                Section.Code("0x00"),
            ],
        ),
        "ef0001 01 0001 02 0001 0001 04 0000 00 00 00",
    ),
    (
        "EIP-4750 Single code section oversized type",
        Container(
            sections=[
                Section(
                    kind=SectionKind.TYPE,
                    data="0x0000000000",
                ),
                Section.Code("0x00"),
            ],
        ),
        "ef0001 01 0005 02 0001 0001 04 0000 00 0000000000 00",
    ),
    (
        "Empty type section",
        Container(
            sections=[
                Section(kind=SectionKind.TYPE, data="0x"),
                Section.Code("0x00"),
            ],
            auto_type_section=AutoSection.NONE,
        ),
        "ef0001 01 0000 02 0001 0001 04 0000 00 00",
    ),
    (
        "Check that simple valid EOF1 deploys",
        Container(
            sections=[
                Section.Code(
                    "0x305000",
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=1,
                ),
                Section.Data("0xef"),
            ],
            auto_type_section=AutoSection.AUTO,
        ),
        """
        # EOF deployed code
        ef0001  # Magic followed by version
        010004  # One code segment
        020001  # One code segment
            0003  #   code seg 0: 3 bytes
        040001  # One byte data segment
        00      # End of header
                # Code segment 0 header
            00  # Zero inputs
            80  # Non-Returning Function
            0001  # Max stack height 1
                # Code segment 0 code
            30 #  1 ADDRESS
            50 #  2 POP
            00 #  3 STOP
            # Data segment
            ef
        """,
    ),
    (
        "Data Section custom_size parameter overwrites bytes size",
        Container(
            sections=[
                Section.Code(
                    "0x305000",
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=1,
                ),
                Section.Data("0x0bad", custom_size=4),
            ],
            auto_type_section=AutoSection.AUTO,
        ),
        """
      # EOF deployed code
      ef0001  # Magic followed by version
      010004  # One code segment
      020001  # One code segment
        0003  #   code seg 0: 3 bytes
      040004  # Four byte data segment
      00      # End of header
              # Code segment 0 header
          00  # Zero inputs
          80  # Non-Returning Function
        0001  # Max stack height 1
              # Code segment 0 code
           30 #  1 ADDRESS
           50 #  2 POP
           00 #  3 STOP
              # Data segment
           0bad  # 2 bytes instead of four
        """,
    ),
    (
        "Multiple code segments",
        Container(
            sections=[
                Section.Code(
                    "0x5f35e2030000000300060009e50001e50002e50003e3000400",
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=1,
                ),
                Section.Code(
                    "0x5f5ff3",
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=2,
                ),
                Section.Code(
                    "0x5f5ffd",
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=2,
                ),
                Section.Code(
                    "0xfe",
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=0,
                ),
                Section.Code(
                    "0xe4",
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=0,
                ),
                Section.Data("0x0bad60a7", custom_size=4),
            ],
            auto_type_section=AutoSection.AUTO,
        ),
        """
      # EOF deployed code
      EF0001 # Magic and Version ( 1 )
     010014 # Types length ( 20 )
     020005 # Total code sections ( 5 )
       0019 # Code section  0 , 25  bytes
       0003 # Code section  1 , 3  bytes
       0003 # Code section  2 , 3  bytes
       0001 # Code section  3 , 1  bytes
       0001 # Code section  4 , 1  bytes
     040004 # Data section length ( 4 )
         00 # Terminator (end of header)
            # Code 0 types
         00 # 0 inputs
         80 # 0 outputs (Non-returning function)
       0001 # max stack: 1
            # Code 1 types
         00 # 0 inputs
         80 # 0 outputs (Non-returning function)
       0002 # max stack: 2
            # Code 2 types
         00 # 0 inputs
         80 # 0 outputs (Non-returning function)
       0002 # max stack: 2
            # Code 3 types
         00 # 0 inputs
         80 # 0 outputs (Non-returning function)
       0000 # max stack: 0
            # Code 4 types
         00 # 0 inputs
         00 # 0 outputs
       0000 # max stack: 0
            # Code section 0
         5f # [0] PUSH0
         35 # [1] CALLDATALOAD
     e2030000000300060009 # [2] RJUMPV(0,3,6,9)
     e50001 # [12] JUMPF(1)
     e50002 # [15] JUMPF(2)
     e50003 # [18] JUMPF(3)
     e30004 # [21] CALLF(4)
         00 # [24] STOP
            # Code section 1
         5f # [0] PUSH0
         5f # [1] PUSH0
         f3 # [2] RETURN
            # Code section 2
         5f # [0] PUSH0
         5f # [1] PUSH0
         fd # [2] REVERT
            # Code section 3
         fe # [0] INVALID
            # Code section 4
         e4 # [0] RETF
            # Data section
     0bad60a7
        """,
    ),
    (
        "Custom Types Section overrides code",
        Container(
            sections=[
                Section(kind=SectionKind.TYPE, data="0x00700002", custom_size=8),
                Section(
                    kind=SectionKind.CODE,
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=1,
                    data="0x305000",
                ),
                Section(kind=SectionKind.DATA, data="0x0bad60A7"),
            ],
        ),
        """
      # EOF deployed code
      ef0001  # Magic followed by version
      010008  # Two code segments
      020001  # One code segment
        0003  #   code seg 0: 3 bytes
      040004  # Four byte data segment
      00      # End of header
              # Code segment 0 header
          00  # Zero inputs
          70  # Non-Returning Function
        0002  # Max stack height 1
              # Code segment 0 code
           30 #  1 ADDRESS
           50 #  2 POP
           00 #  3 STOP
              # Data segment
           0bad60A7  # 4 bytes (valid)
        """,
    ),
    (
        "Type section wrong order, but only in HEADER",
        Container(
            sections=[
                Section(
                    kind=SectionKind.CODE,
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=1,
                    data="0x305000",
                ),
                Section(
                    kind=SectionKind.TYPE,
                    data="0x00800001",
                ),
                Section(kind=SectionKind.DATA, data="0xef"),
            ],
            auto_sort_sections=AutoSection.ONLY_BODY,
        ),
        """
      # EOF deployed code
      ef0001  # Magic followed by version
      020001  # One code segment
        0003  #   code seg 0: 3 bytes
      010004  # One code segment
      040001  # One byte data segment
      00      # End of header
              # Code segment 0 header
          00  # Zero inputs
          80  # Non-Returning Function
        0001  # Max stack height 1
              # Code segment 0 code
           30 #  1 ADDRESS
           50 #  2 POP
           00 #  3 STOP
              # Data segment
           ef
        """,
    ),
    (
        "Type section wrong order, but only in BODY",
        Container(
            sections=[
                Section(
                    kind=SectionKind.CODE,
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=1,
                    data="0x305000",
                ),
                Section(
                    kind=SectionKind.TYPE,
                    data="0x00800001",
                ),
                Section(kind=SectionKind.DATA, data="0xef"),
            ],
            auto_sort_sections=AutoSection.ONLY_HEADER,
        ),
        """
      # EOF deployed code
      ef0001  # Magic followed by version
      010004  # One code segment
      020001  # One code segment
        0003  #   code seg 0: 3 bytes
      040001  # One byte data segment
      00      # End of header
              # Code segment 0 code
           30 #  1 ADDRESS
           50 #  2 POP
           00 #  3 STOP
              # Code segment 0 header
          00  # Zero inputs
          80  # Non-Returning Function
        0001  # Max stack height 1
              # Data segment
           ef
        """,
    ),
    (
        "Type section missing, but only in HEADER",
        Container(
            sections=[
                Section(
                    kind=SectionKind.CODE,
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=1,
                    data="0x305000",
                ),
                Section(kind=SectionKind.DATA, data="0xef"),
            ],
            auto_type_section=AutoSection.ONLY_BODY,
        ),
        """
      # EOF deployed code
      ef0001  # Magic followed by version
      020001  # One code segment
        0003  #   code seg 0: 3 bytes
      040001  # One byte data segment
      00      # End of header
              # Code segment 0 header
          00  # Zero inputs
          80  # Non-Returning Function
        0001  # Max stack height 1
              # Code segment 0 code
           30 #  1 ADDRESS
           50 #  2 POP
           00 #  3 STOP
              # Data segment
           ef
        """,
    ),
    (
        "Type section missing, but only in BODY",
        Container(
            sections=[
                Section(
                    kind=SectionKind.CODE,
                    code_inputs=0,
                    code_outputs=128,  # Non returning
                    max_stack_height=1,
                    data="0x305000",
                ),
                Section(kind=SectionKind.DATA, data="0xef"),
            ],
            auto_type_section=AutoSection.ONLY_HEADER,
        ),
        """
      # EOF deployed code
      ef0001  # Magic followed by version
      010004  # Types section
      020001  # One code segment
        0003  #   code seg 0: 3 bytes
      040001  # One byte data segment
      00      # End of header
              # Code segment 0 header
              # Code segment 0 code
           30 #  1 ADDRESS
           50 #  2 POP
           00 #  3 STOP
              # Data segment
           ef
        """,
    ),
    (
        "Container.Init simple test",
        Container.Init(deploy_container=Container.Code(b"\0")),
        """
      # EOF deployed code
      ef0001  # Magic followed by version
      010004  # Types section
      020001  # One code segment
        0006  #   code seg 0: 6 bytes
      030001  # One container segment
        0014  #   container seg 0: 20 bytes
      040000  # Zero byte data segment
      00      # End of header
   0080 0002  # Types section
              # Code segment 0 code
         6000 #  1 PUSH1 0
         6000 #  2 PUSH1 0
         ee00 #  3 RETURNCONTRACT[0]
              # Subcontainer 0
      ef0001  # Magic followed by version
      010004  # Types section
      020001  # One code segment
        0001  #   code seg 0: 1 byte
      040000  # Zero byte data segment
      00      # End of header
   0080 0000  # Types section
              # Code segment 0 code
           00 #  1 STOP
        """,
    ),
    (
        "Container.Init initcode prefix",
        Container.Init(deploy_container=Container.Code(b"\0"), initcode_prefix=Op.SSTORE(0, 0)),
        """
      # EOF deployed code
      ef0001  # Magic followed by version
      010004  # Types section
      020001  # One code segment
        000b  #   code seg 0: 11 bytes
      030001  # One container segment
        0014  #   container seg 0: 20 bytes
      040000  # Zero byte data segment
      00      # End of header
   0080 0002  # Types section
              # Code segment 0 code
         6000 #  1 PUSH1 0
         6000 #  2 PUSH1 0
           55 #  3 SSTORE
         6000 #  4 PUSH1 0
         6000 #  5 PUSH1 0
         ee00 #  6 RETURNCONTRACT[0]
              # Subcontainer 0
      ef0001  # Magic followed by version
      010004  # Types section
      020001  # One code segment
        0001  #   code seg 0: 1 byte
      040000  # Zero byte data segment
      00      # End of header
   0080 0000  # Types section
              # Code segment 0 code
           00 #  1 STOP
        """,
    ),
]


@pytest.mark.parametrize(
    ["container", "hex"],
    [(x[1], x[2]) for x in test_cases],
    ids=[x[0] for x in test_cases],
)
def test_eof_v1_assemble(container: Container, hex: str):
    """
    Test `ethereum_test.types.code`.
    """
    expected_string = remove_comments_from_string(hex)
    expected_bytes = bytes.fromhex(expected_string.replace(" ", "").replace("\n", ""))
    assert (
        bytes(container) == expected_bytes
    ), f"""
    Container: {bytes(container).hex()}
    Expected : {expected_bytes.hex()}
    """


def remove_comments_from_string(input_string):
    """
    Remove comments from a string and leave only valid hex characters.
    """
    # Split the string into individual lines
    lines = input_string.split("\n")

    # Process each line to remove text following a '#'
    cleaned_lines = []
    for line in lines:
        # Find the index of the first '#' character
        comment_start = line.find("#")

        # If a '#' is found, slice up to that point; otherwise, take the whole line
        if comment_start != -1:
            cleaned_line = line[:comment_start].rstrip()
        else:
            cleaned_line = line

        # Only add non-empty lines if needed
        if cleaned_line.strip():
            cleaned_lines.append(cleaned_line)

    # Join the cleaned lines back into a single string
    cleaned_string = "\n".join(cleaned_lines)
    return cleaned_string


@pytest.mark.parametrize(
    "model",
    [
        Container(),
    ],
    ids=lambda model: model.__class__.__name__,
)
def test_model_copy(model: CopyValidateModel):
    """
    Test that the copy method returns a correct copy of the model.
    """
    assert to_json(model.copy()) == to_json(model)
    assert model.copy().model_fields_set == model.model_fields_set
