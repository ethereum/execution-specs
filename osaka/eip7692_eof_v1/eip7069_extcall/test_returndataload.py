"""
abstract: Tests [EIP-7069: Revamped CALL instructions](https://eips.ethereum.org/EIPS/eip-7069)
    Tests for the RETURNDATALOAD instriction
"""  # noqa: E501
import pytest

from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Storage, Transaction
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from . import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION
from .helpers import (
    slot_code_worked,
    slot_eof_target_call_status,
    slot_eof_target_returndata,
    slot_eof_target_returndatasize,
    slot_legacy_target_call_status,
    slot_legacy_target_returndatasize,
    value_code_worked,
    value_exceptional_abort_canary,
)
from .spec import EXTCALL_FAILURE, EXTCALL_SUCCESS, LEGACY_CALL_FAILURE, LEGACY_CALL_SUCCESS

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALL,
        Op.CALLCODE,
        Op.DELEGATECALL,
        Op.STATICCALL,
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
@pytest.mark.parametrize(
    "return_data",
    [
        b"",
        b"\x10" * 0x10,
        b"\x20" * 0x20,
        b"\x30" * 0x30,
    ],
    ids=lambda x: "len_%x" % len(x),
)
@pytest.mark.parametrize(
    "offset",
    [
        0,
        0x10,
        0x20,
        0x30,
    ],
    ids=lambda x: "offset_%x" % x,
)
@pytest.mark.parametrize(
    "size",
    [
        0,
        0x10,
        0x20,
        0x30,
    ],
    ids=lambda x: "size_%x" % x,
)
def test_returndatacopy_handling(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    return_data: bytes,
    offset: int,
    size: int,
):
    """
    Tests ReturnDataLoad including multiple offset conditions and differeing legacy vs. eof
    boundary conditions.

    entrypoint creates a "0xff" test area of memory, delegate calls to caller.
    Caller is either EOF or legacy, as per parameter.  Calls returner and copies the return data
    based on offset and size params.  Cases are expected to trigger boundary violations.

    Entrypoint copies the test area to storage slots, and the expected result is asserted.
    """
    env = Environment()

    slot_result_start = 0x1000

    sender = pre.fund_eoa()

    address_returner = pre.deploy_contract(
        Container(
            sections=[
                Section.Code(
                    code=Op.DATACOPY(0, 0, Op.DATASIZE) + Op.RETURN(0, Op.DATASIZE),
                ),
                Section.Data(data=return_data),
            ]
        )
    )

    result = [0xFF] * 0x40
    result[0:size] = [0] * size
    extent = size - max(0, size + offset - len(return_data))
    if extent > 0 and len(return_data) > 0:
        result[0:extent] = [return_data[0]] * extent

    code_under_test = (
        opcode(address=address_returner)
        + Op.RETURNDATACOPY(0, offset, size)
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.RETURN(0, size)
    )
    match opcode:
        case Op.EXTCALL | Op.EXTDELEGATECALL | Op.EXTSTATICCALL:
            address_caller = pre.deploy_contract(
                Container(
                    sections=[
                        Section.Code(
                            code=code_under_test,
                        )
                    ]
                )
            )
        case Op.CALL | Op.CALLCODE | Op.DELEGATECALL | Op.STATICCALL:
            address_caller = pre.deploy_contract(code_under_test)

    address_entry_point = pre.deploy_contract(
        Op.NOOP
        # First, create a "dirty" area, so we can check zero overwrite
        + Op.MSTORE(0x00, -1)
        + Op.MSTORE(0x20, -1)
        # call the contract under test
        + Op.DELEGATECALL(1_000_000, address_caller, 0, 0, 0, 0)
        + Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE)
        # store the return data
        + Op.SSTORE(slot_result_start, Op.MLOAD(0x0))
        + Op.SSTORE(slot_result_start + 1, Op.MLOAD(0x20))
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP,
    )

    post = {
        address_entry_point: Account(
            storage={
                slot_code_worked: value_code_worked,
                slot_result_start: bytes(result[:0x20]),
                (slot_result_start + 0x1): bytes(result[0x20:]),
            }
        )
    }
    if opcode in [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL] and (
        (offset + size) > len(return_data)
    ):
        post[address_entry_point] = Account(
            storage={
                slot_code_worked: value_code_worked,
                slot_result_start: b"\xff" * 32,
                slot_result_start + 1: b"\xff" * 32,
            }
        )

    tx = Transaction(to=address_entry_point, gas_limit=2_000_000, sender=sender)

    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
@pytest.mark.parametrize(
    "return_data",
    [
        b"",
        b"\x10" * 0x10,
        b"\x20" * 0x20,
        b"\x30" * 0x30,
    ],
    ids=lambda x: "len_%x" % len(x),
)
@pytest.mark.parametrize(
    "offset",
    [
        0,
        0x10,
        0x20,
        0x30,
    ],
    ids=lambda x: "offset_%x" % x,
)
def test_returndataload_handling(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    return_data: bytes,
    offset: int,
):
    """
    Much simpler than returndatacopy, no memory or boosted call.  Returner is called
    and results are stored in storage slot, which is asserted for expected values.
    The parameters offset and return data are configured to test boundary conditions.
    """
    env = Environment()

    slot_result_start = 0x1000

    sender = pre.fund_eoa()
    address_returner = pre.deploy_contract(
        Container(
            sections=[
                Section.Code(
                    code=Op.DATACOPY(0, 0, Op.DATASIZE) + Op.RETURN(0, Op.DATASIZE),
                ),
                Section.Data(data=return_data),
            ]
        )
    )
    address_entry_point = pre.deploy_contract(
        Container(
            sections=[
                Section.Code(
                    code=opcode(address=address_returner)
                    + Op.SSTORE(slot_result_start, Op.RETURNDATALOAD(offset))
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ]
        )
    )

    result = [0] * 0x20
    extent = 0x20 - max(0, 0x20 + offset - len(return_data))
    if extent > 0 and len(return_data) > 0:
        result[0:extent] = [return_data[0]] * extent
    post = {
        address_entry_point: Account(
            storage={
                slot_code_worked: value_code_worked,
                slot_result_start: bytes(result),
            }
        )
    }

    tx = Transaction(to=address_entry_point, gas_limit=2_000_000, sender=sender)

    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALL,
        Op.EXTCALL,
    ],
)
def test_returndatacopy_oob(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
):
    """
    Extends the RETURNDATACOPY test for correct out-of-bounds behavior, by checking if the
    caller frame's context being EOF or legacy doesn't impact the execution logic of the
    RETURNDATACOPY instance under test.
    """
    env = Environment()

    sender = pre.fund_eoa()

    # Both callee codes below make an OOB (out-of-bounds) RETURNDATACOPY of one byte,
    # which they then attempt to return (Legacy should exceptionally halt on RETURNDATACOPY).
    address_callee_eof = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.RETURNDATACOPY(0, 0, 1) + Op.RETURN(0, 1),
                    max_stack_height=3,
                )
            ]
        )
    )
    address_callee_legacy = pre.deploy_contract(Op.RETURNDATACOPY(0, 0, 1) + Op.RETURN(0, 1))

    # Caller code is selected to either be Legacy or EOF using params.
    code_entry_point = (
        Op.SSTORE(slot_eof_target_call_status, opcode(address=address_callee_eof))
        + Op.SSTORE(slot_eof_target_returndatasize, Op.RETURNDATASIZE)
        + Op.SSTORE(slot_eof_target_returndata, Op.RETURNDATACOPY(0, 0, 1) + Op.MLOAD(0))
        + Op.SSTORE(
            slot_legacy_target_call_status,
            opcode(address=address_callee_legacy),
        )
        + Op.SSTORE(slot_legacy_target_returndatasize, Op.RETURNDATASIZE)
        + Op.STOP
    )

    storage_entry_point = Storage(
        {
            slot_eof_target_call_status: value_exceptional_abort_canary,
            slot_eof_target_returndata: value_exceptional_abort_canary,
            slot_eof_target_returndatasize: value_exceptional_abort_canary,
            slot_legacy_target_call_status: value_exceptional_abort_canary,
            slot_legacy_target_returndatasize: value_exceptional_abort_canary,
        }
    )

    address_entry_point = (
        pre.deploy_contract(code=code_entry_point, storage=storage_entry_point)
        if opcode == Op.CALL
        else pre.deploy_contract(
            Container(
                sections=[
                    Section.Code(
                        code=code_entry_point,
                        max_stack_height=4,
                        storage=storage_entry_point,
                    )
                ]
            )
        )
    )

    tx = Transaction(to=address_entry_point, gas_limit=2_000_000, sender=sender)

    post = {
        address_entry_point: Account(
            storage={
                slot_eof_target_call_status: LEGACY_CALL_SUCCESS,
                slot_eof_target_returndata: "0x00",
                slot_eof_target_returndatasize: "0x01",
                slot_legacy_target_call_status: LEGACY_CALL_FAILURE,
                slot_legacy_target_returndatasize: "0x00",
            }
            if opcode == Op.CALL
            else {
                slot_eof_target_call_status: EXTCALL_SUCCESS,
                slot_eof_target_returndata: "0x00",
                slot_eof_target_returndatasize: "0x01",
                slot_legacy_target_call_status: EXTCALL_FAILURE,
                slot_legacy_target_returndatasize: "0x00",
            }
        )
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
