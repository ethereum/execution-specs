"""EOF Container construction test."""

import pytest

from ethereum_test_exceptions.exceptions import EOFExceptionInstanceOrList
from ethereum_test_tools import EOFException, EOFTestFiller, extend_with_defaults
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types.eof.v1 import Container, Section

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    **extend_with_defaults(
        defaults={
            "skip_header_listing": False,  # second section is mentioned in code header array
            "skip_body_listing": False,  # second section code is in container's body
            "skip_types_body_listing": False,  # code input bytes not listed in container's body
            "skip_types_header_listing": False,  # code input bytes size not added to types section size  # noqa: E501
            "expected_code": "",
            "expected_exception": None,
        },
        cases=[
            pytest.param(
                {
                    "skip_header_listing": True,
                    "skip_body_listing": True,
                    "expected_code": "ef00010100080200010003ff00040000800001000000003050000bad60A7",  # noqa: E501
                    "expected_exception": [
                        EOFException.INVALID_TYPE_SECTION_SIZE,
                        EOFException.INVALID_SECTION_BODIES_SIZE,
                    ],
                },
                id="drop_code_section_and_header",
            ),
            pytest.param(
                {
                    "skip_header_listing": True,
                    "skip_body_listing": False,
                    "expected_code": "ef00010100080200010003ff00040000800001000000003050003050000bad60A7",  # noqa: E501
                    "expected_exception": [
                        EOFException.INVALID_TYPE_SECTION_SIZE,
                        EOFException.INVALID_SECTION_BODIES_SIZE,
                    ],
                },
                id="drop_code_header",
            ),
            pytest.param(
                {
                    "skip_header_listing": False,
                    "skip_body_listing": True,
                    "expected_code": "ef000101000802000200030003ff00040000800001000000003050000bad60A7",  # noqa: E501
                    "expected_exception": [
                        EOFException.UNREACHABLE_CODE_SECTIONS,
                        EOFException.TOPLEVEL_CONTAINER_TRUNCATED,
                    ],
                },
                id="drop_code_section",
            ),
            pytest.param(
                {
                    "skip_header_listing": False,
                    "skip_body_listing": False,
                    "expected_code": "ef000101000802000200030003ff00040000800001000000003050003050000bad60A7",  # noqa: E501
                    "expected_exception": EOFException.UNREACHABLE_CODE_SECTIONS,
                },
                id="layout_ok_code_bad",
            ),
            pytest.param(
                {
                    "skip_header_listing": True,
                    "skip_body_listing": True,
                    "skip_types_body_listing": True,
                    "expected_code": "ef00010100080200010003ff000400008000013050000bad60a7",
                    "expected_exception": [
                        EOFException.INVALID_TYPE_SECTION_SIZE,
                        EOFException.INVALID_SECTION_BODIES_SIZE,
                    ],
                },
                id="drop_types_header",
            ),
            pytest.param(
                {
                    "skip_header_listing": True,
                    "skip_body_listing": True,
                    "skip_types_body_listing": True,
                    "skip_types_header_listing": True,
                    "expected_code": "ef00010100040200010003ff000400008000013050000bad60a7",
                    "expected_exception": None,
                },
                id="drop_everything",
            ),
        ],
    )
)
def test_code_section_header_body_mismatch(
    eof_test: EOFTestFiller,
    skip_header_listing: bool,
    skip_body_listing: bool,
    skip_types_body_listing: bool,
    skip_types_header_listing: bool,
    expected_code: str,
    expected_exception: EOFExceptionInstanceOrList | None,
):
    """Inconsistent number of code sections (between types and code)."""
    eof_code = Container(
        name="EOF1I0018",
        sections=[
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
            ),
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
                # whether to not mention it in code section header list
                skip_header_listing=skip_header_listing,
                # whether to not print its code in containers body
                skip_body_listing=skip_body_listing,
                # whether to not print its input bytes in containers body
                skip_types_body_listing=skip_types_body_listing,
                # whether to not calculate its input bytes size in types section's header
                skip_types_header_listing=skip_types_header_listing,
            ),
            Section.Data("0x0bad60A7"),
        ],
    )

    # TODO remove this after Container class implementation is reliable
    assert bytes(eof_code).hex() == bytes.fromhex(expected_code).hex()

    eof_test(
        container=eof_code,
        expect_exception=expected_exception,
    )
