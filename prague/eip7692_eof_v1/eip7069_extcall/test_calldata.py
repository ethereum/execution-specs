"""
abstract: Tests [EIP-7069: Revamped CALL instructions](https://eips.ethereum.org/EIPS/eip-7069)
    Tests for the RETURNDATALOAD instriction
"""  # noqa: E501

import pytest

from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from . import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION
from .helpers import (
    slot_call_status,
    slot_calldata_1,
    slot_calldata_2,
    slot_code_worked,
    slot_delegate_code_worked,
    value_code_worked,
    value_exceptional_abort_canary,
)
from .spec import EXTCALL_SUCCESS

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def right_pad_32(v: bytes) -> bytes:
    """Takes bytes and returns a 32 byte version right padded with zeros"""
    return v + b"\0" * (32 - len(v))


@pytest.mark.parametrize("value", [0, 1])
@pytest.mark.parametrize(
    "memory",
    [
        b"",
        b"1234567890abcdef",
        b"1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=-",
        b"1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=-" * 4,
    ],
    ids=lambda x: "size_%d" % len(x),
)
@pytest.mark.parametrize("offset", [0, 8, 24, 80])
@pytest.mark.parametrize("length", [0, 8, 32, 48])
def test_extcalls_inputdata(
    state_test: StateTestFiller,
    pre: Alloc,
    value: int,
    memory: bytes,
    offset: int,
    length: int,
):
    """
    Tests call data into EXT*CALL including multiple offset conditions.

    Caller pushes data into memory, then calls the target.  Target writes 64 bytes of call data
    to storage and a success byte.
    """
    env = Environment()

    sender = pre.fund_eoa(10**18)

    address_returner = pre.deploy_contract(
        Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(slot_calldata_1, Op.CALLDATALOAD(0))
                    + Op.SSTORE(slot_calldata_2, Op.CALLDATALOAD(32))
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP
                ),
            ]
        ),
    )
    address_caller = pre.deploy_contract(
        Container(
            sections=[
                Section.Code(
                    code=Op.DATACOPY(0, 0, len(memory))
                    + Op.SSTORE(
                        slot_call_status,
                        Op.EXTCALL(address_returner, offset, length, value),
                    )
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP
                ),
                Section.Data(data=memory),
            ]
        ),
        storage={slot_call_status: value_exceptional_abort_canary},
        balance=10**9,
    )

    calldata = memory[offset : offset + length]
    post = {
        address_returner: Account(
            storage={
                slot_code_worked: value_code_worked,
                slot_calldata_1: right_pad_32(calldata[0:32]),
                slot_calldata_2: right_pad_32(calldata[32:64]),
            }
        ),
        address_caller: Account(
            storage={
                slot_code_worked: value_code_worked,
                slot_call_status: EXTCALL_SUCCESS,
            }
        ),
    }

    tx = Transaction(to=address_caller, gas_limit=2_000_000, sender=sender)

    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "memory",
    [
        b"",
        b"1234567890abcdef",
        b"1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=-",
        b"1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=-" * 4,
    ],
    ids=lambda x: "size_%d" % len(x),
)
@pytest.mark.parametrize("offset", [0, 8, 24, 80])
@pytest.mark.parametrize("length", [0, 8, 32, 48])
def test_extdelegatecall_inputdata(
    state_test: StateTestFiller,
    pre: Alloc,
    memory: bytes,
    offset: int,
    length: int,
):
    """
    Tests call data into EXT*CALL including multiple offset conditions.

    Caller pushes data into memory, then calls the target.  Target writes 64 bytes of call data
    to storage and a success byte.
    """
    env = Environment()

    sender = pre.fund_eoa(10**18)

    address_returner = pre.deploy_contract(
        Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(slot_calldata_1, Op.CALLDATALOAD(0))
                    + Op.SSTORE(slot_calldata_2, Op.CALLDATALOAD(32))
                    + Op.SSTORE(slot_delegate_code_worked, value_code_worked)
                    + Op.STOP
                ),
            ]
        ),
    )
    address_caller = pre.deploy_contract(
        Container(
            sections=[
                Section.Code(
                    code=Op.DATACOPY(0, 0, len(memory))
                    + Op.SSTORE(
                        slot_call_status,
                        Op.EXTDELEGATECALL(address_returner, offset, length),
                    )
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP
                ),
                Section.Data(data=memory),
            ]
        ),
        storage={slot_call_status: value_exceptional_abort_canary},
        balance=10**9,
    )

    calldata = memory[offset : offset + length]
    post = {
        address_returner: Account(storage={}),
        address_caller: Account(
            storage={
                slot_code_worked: value_code_worked,
                slot_delegate_code_worked: value_code_worked,
                slot_call_status: EXTCALL_SUCCESS,
                slot_calldata_1: right_pad_32(calldata[0:32]),
                slot_calldata_2: right_pad_32(calldata[32:64]),
            }
        ),
    }

    tx = Transaction(to=address_caller, gas_limit=2_000_000, sender=sender)

    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "memory",
    [
        b"",
        b"1234567890abcdef",
        b"1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=-",
        b"1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=-" * 4,
    ],
    ids=lambda x: "size_%d" % len(x),
)
@pytest.mark.parametrize("offset", [0, 8, 24, 80])
@pytest.mark.parametrize("length", [0, 8, 32, 48])
def test_extstaticcall_inputdata(
    state_test: StateTestFiller,
    pre: Alloc,
    memory: bytes,
    offset: int,
    length: int,
):
    """
    Tests call data into EXT*CALL including multiple offset conditions.

    Caller pushes data into memory, then calls the target.  Target writes 64 bytes of call data
    to storage and a success byte.
    """
    env = Environment()

    sender = pre.fund_eoa(10**18)

    address_returner = pre.deploy_contract(
        Container(
            sections=[
                Section.Code(
                    code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.RETURN(0, Op.CALLDATASIZE)
                ),
            ]
        ),
    )
    address_caller = pre.deploy_contract(
        Container(
            sections=[
                Section.Code(
                    code=Op.DATACOPY(0, 0, len(memory))
                    + Op.SSTORE(
                        slot_call_status,
                        Op.EXTSTATICCALL(address_returner, offset, length),
                    )
                    + Op.SSTORE(slot_calldata_1, Op.RETURNDATALOAD(0))
                    + Op.SSTORE(slot_calldata_2, Op.RETURNDATALOAD(32))
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP
                ),
                Section.Data(data=memory),
            ]
        ),
        storage={slot_call_status: value_exceptional_abort_canary},
        balance=10**9,
    )

    calldata = memory[offset : offset + length]
    post = {
        address_returner: Account(storage={}),
        address_caller: Account(
            storage={
                slot_code_worked: value_code_worked,
                slot_call_status: EXTCALL_SUCCESS,
                slot_calldata_1: right_pad_32(calldata[0:32]),
                slot_calldata_2: right_pad_32(calldata[32:64]),
            }
        ),
    }

    tx = Transaction(to=address_caller, gas_limit=2_000_000, sender=sender)

    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )
