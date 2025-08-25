"""Tests for RETURNCODE instruction validation."""

import pytest

from ethereum_test_base_types import Account
from ethereum_test_specs import StateTestFiller
from ethereum_test_tools import Alloc, EOFException, EOFTestFiller
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types import Environment, Transaction, compute_eofcreate_address
from ethereum_test_types.eof.v1 import Container, ContainerKind, Section
from ethereum_test_types.eof.v1.constants import MAX_BYTECODE_SIZE

from .. import EOF_FORK_NAME
from .helpers import (
    slot_create_address,
    smallest_runtime_subcontainer,
    value_canary_to_be_overwritten,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7620.md"
REFERENCE_SPEC_VERSION = "f20b164b00ae5553f7536a6d7a83a0f254455e09"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def test_returncode_valid_index_0(
    eof_test: EOFTestFiller,
):
    """Deploy container index 0."""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        container=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCODE[0](0, 0),
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
    )


def test_returncode_valid_index_1(
    eof_test: EOFTestFiller,
):
    """Deploy container index 1."""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        container=Container(
            sections=[
                Section.Code(
                    code=Op.RJUMPI[6](0) + Op.RETURNCODE[0](0, 0) + Op.RETURNCODE[1](0, 0),
                    max_stack_height=2,
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
    )


def test_returncode_valid_index_255(
    eof_test: EOFTestFiller,
):
    """Deploy container index 255."""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        container=Container(
            sections=[
                Section.Code(
                    sum((Op.RJUMPI[6](0) + Op.RETURNCODE[i](0, 0)) for i in range(256))
                    + Op.REVERT(0, 0),
                    max_stack_height=2,
                )
            ]
            + [Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)]))]
            * 256
        ),
    )


def test_returncode_invalid_truncated_immediate(
    eof_test: EOFTestFiller,
):
    """Truncated immediate."""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.PUSH0 + Op.RETURNCODE,
                ),
            ],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


def test_returncode_invalid_index_0(
    eof_test: EOFTestFiller,
):
    """Referring to non-existent container section index 0."""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        container=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCODE[0](0, 0),
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_CONTAINER_SECTION_INDEX,
    )


def test_returncode_invalid_index_1(
    eof_test: EOFTestFiller,
):
    """Referring to non-existent container section index 1."""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        container=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCODE[1](0, 0),
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
        expect_exception=EOFException.INVALID_CONTAINER_SECTION_INDEX,
    )


def test_returncode_invalid_index_255(
    eof_test: EOFTestFiller,
):
    """Referring to non-existent container section index 255."""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        container=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCODE[255](0, 0),
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
        expect_exception=EOFException.INVALID_CONTAINER_SECTION_INDEX,
    )


def test_returncode_terminating(
    eof_test: EOFTestFiller,
):
    """Unreachable code after RETURNCODE."""
    eof_test(
        container_kind=ContainerKind.INITCODE,
        container=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNCODE[0](0, 0) + Op.REVERT(0, 0),
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
        expect_exception=EOFException.UNREACHABLE_INSTRUCTIONS,
    )


@pytest.mark.parametrize(
    "offset_field",
    [
        pytest.param(True, id="offset"),
        pytest.param(False, id="size"),
    ],
)
@pytest.mark.parametrize(
    ("test_arg", "success"),
    [
        pytest.param(0, True, id="zero"),
        pytest.param(0xFF, True, id="8-bit"),
        pytest.param(0x100, True, id="9-bit"),
        pytest.param(0xFFFF, True, id="16-bit"),
        pytest.param(0x10000, True, id="17-bit"),
        pytest.param(0x1FFFF20, False, id="32-bit-mem-cost"),
        pytest.param(0x2D412E0, False, id="33-bit-mem-cost"),
        pytest.param(0xFFFFFFFF, False, id="32-bit"),
        pytest.param(0x100000000, False, id="33-bit"),
        pytest.param(0x1FFFFFFFF20, False, id="64-bit-mem-cost"),
        pytest.param(0x2D413CCCF00, False, id="65-bit-mem-cost"),
        pytest.param(0xFFFFFFFFFFFFFFFF, False, id="64-bit"),
        pytest.param(0x10000000000000000, False, id="65-bit"),
        pytest.param(0xFFFFFFFFFFFFFFFF, False, id="128-bit"),
        pytest.param(0x10000000000000000, False, id="129-bit"),
        pytest.param(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, False, id="256-bit"),
    ],
)
def test_returncode_memory_expansion(
    state_test: StateTestFiller,
    pre: Alloc,
    offset_field: str,
    test_arg: int,
    success: bool,
):
    """
    Attempts an EOFCREATE with a possibly too-large auxdata.  Create either fails due to gas
    or contract too large, resulting in address or zero on failure in the create address slot.

    The name id of `*-mem-cost` refers to the bit-length of the result of the calculated memory
    expansion cost. Their length choice is designed to cause problems on shorter bit-length
    representations with native integers.

    The `offset_field` param indicates what part of the input data arguments are being tested,
    either the offset of the data in memory or the size of the data in memory.

    The `test_arg` param is the value passed into the field being tested (offset or size),
    intending to trigger integer size bugs for that particular field.
    """
    env = Environment(gas_limit=2_000_000_000)
    sender = pre.fund_eoa(10**27)

    eof_size_acceptable = offset_field or test_arg < MAX_BYTECODE_SIZE

    mem_size_initcode_container = Container(
        sections=[
            Section.Code(
                code=Op.RETURNCODE[0](
                    auxdata_offset=test_arg if offset_field else 32,
                    auxdata_size=32 if offset_field else test_arg,
                )
            ),
            Section.Container(container=smallest_runtime_subcontainer),
        ],
    )
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, 0)) + Op.STOP,
                ),
                Section.Container(container=mem_size_initcode_container),
            ],
        ),
        storage={
            slot_create_address: value_canary_to_be_overwritten,
        },
    )
    # Storage in 0 should have the address,
    post = {
        contract_address: Account(
            storage={
                slot_create_address: compute_eofcreate_address(contract_address, 0)
                if success and eof_size_acceptable
                else 0,
            }
        )
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=2_000_000_000,
        gas_price=10,
        protected=False,
        sender=sender,
    )
    state_test(env=env, pre=pre, post=post, tx=tx)
