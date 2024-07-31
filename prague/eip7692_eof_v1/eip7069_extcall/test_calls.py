"""
test calls across EOF and Legacy
"""
import itertools

import pytest

from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Storage,
    Transaction,
)
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)
REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "2f013de4065babde7c02f84a2ce9864a3c5bfbd3"

"""Storage addresses for common testing fields"""
_slot = itertools.count(1)
slot_code_worked = next(_slot)
slot_call_result = next(_slot)
slot_returndata = next(_slot)
slot_returndatasize = next(_slot)
slot_caller = next(_slot)
slot_returndatasize_before_clear = next(_slot)
slot_last_slot = next(_slot)

"""Storage values for common testing fields"""
value_code_worked = 0x2015
value_legacy_call_worked = 1
value_legacy_call_failed = 0
value_eof_call_worked = 0
value_eof_call_reverted = 1
value_eof_call_failed = 2
value_returndata_magic = b"\x42"


contract_eof_sstore = Container(
    sections=[
        Section.Code(
            code=Op.SSTORE(slot_caller, Op.CALLER()) + Op.STOP,
        )
    ]
)


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """
    The sender of the transaction
    """
    return pre.fund_eoa()


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALL,
        Op.DELEGATECALL,
        Op.CALLCODE,
        Op.STATICCALL,
    ],
)
def test_legacy_calls_eof_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test legacy contracts calling EOF contracts that use SSTORE"""
    env = Environment()
    destination_contract_address = pre.deploy_contract(contract_eof_sstore)

    caller_contract = Op.SSTORE(
        slot_call_result, opcode(address=destination_contract_address)
    ) + Op.SSTORE(slot_code_worked, value_code_worked)

    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = Storage(
        {
            slot_code_worked: value_code_worked,  # type: ignore
            slot_call_result: value_legacy_call_worked,  # type: ignore
        }
    )
    destination_storage = Storage()

    if opcode == Op.CALL:
        destination_storage[slot_caller] = calling_contract_address
    elif opcode == Op.DELEGATECALL:
        calling_storage[slot_caller] = sender
    elif opcode == Op.CALLCODE:
        calling_storage[slot_caller] = calling_contract_address
    elif opcode == Op.STATICCALL:
        calling_storage[slot_call_result] = value_legacy_call_failed

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage=destination_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALL,
        Op.DELEGATECALL,
        Op.CALLCODE,
        Op.STATICCALL,
    ],
)
def test_legacy_calls_eof_mstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test legacy contracts calling EOF contracts that only return data"""
    env = Environment()
    destination_contract_code = Container(
        sections=[
            Section.Code(
                code=Op.MSTORE8(0, int.from_bytes(value_returndata_magic, "big"))
                + Op.RETURN(0, len(value_returndata_magic)),
            )
        ]
    )
    destination_contract_address = pre.deploy_contract(destination_contract_code)

    caller_contract = (
        Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
        + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(31, 0, 1)
        + Op.SSTORE(slot_returndata, Op.MLOAD(0))
        + Op.SSTORE(slot_code_worked, value_code_worked)
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,  # type: ignore
        slot_call_result: value_legacy_call_worked,  # type: ignore
        slot_returndatasize: len(value_returndata_magic),  # type: ignore
        slot_returndata: value_returndata_magic,  # type: ignore
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage={}),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
def test_eof_calls_eof_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test EOF contracts calling EOF contracts that use SSTORE"""
    env = Environment()
    destination_contract_address = pre.deploy_contract(contract_eof_sstore)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
            )
        ]
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = Storage(
        {
            slot_code_worked: value_code_worked,  # type: ignore
            slot_call_result: value_eof_call_worked,  # type: ignore
        }
    )
    destination_storage = Storage()

    if opcode == Op.EXTCALL:
        destination_storage[slot_caller] = calling_contract_address
    elif opcode == Op.EXTDELEGATECALL:
        calling_storage[slot_caller] = sender
    elif opcode == Op.EXTSTATICCALL:
        calling_storage[slot_call_result] = value_eof_call_failed

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage=destination_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
def test_eof_calls_eof_mstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test EOF contracts calling EOF contracts that return data"""
    env = Environment()
    destination_contract_code = Container(
        sections=[
            Section.Code(
                code=Op.MSTORE8(0, int.from_bytes(value_returndata_magic, "big"))
                + Op.RETURN(0, 32),
            )
        ]
    )
    destination_contract_address = pre.deploy_contract(destination_contract_code)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
                + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
                + Op.SSTORE(slot_returndata, Op.RETURNDATALOAD(0))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
            )
        ]
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,  # type: ignore
        slot_call_result: value_eof_call_worked,  # type: ignore
        slot_returndatasize: 0x20,  # type: ignore
        slot_returndata: value_returndata_magic
        + b"\0" * (0x20 - len(value_returndata_magic)),  # type: ignore
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage={}),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
def test_eof_calls_legacy_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test EOF contracts calling Legacy contracts that use SSTORE"""
    env = Environment()
    destination_contract_code = Op.SSTORE(slot_caller, Op.CALLER()) + Op.STOP
    destination_contract_address = pre.deploy_contract(destination_contract_code)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
            )
        ]
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,  # type: ignore
        slot_call_result: value_eof_call_worked,  # type: ignore
    }
    destination_storage = {}

    if opcode == Op.EXTCALL:
        destination_storage[slot_caller] = calling_contract_address
    elif opcode == Op.EXTDELEGATECALL:
        # EOF delegate call to legacy is a light failure by rule
        calling_storage[slot_call_result] = value_eof_call_reverted
    elif opcode == Op.EXTSTATICCALL:
        calling_storage[slot_call_result] = value_eof_call_failed

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage=destination_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
def test_eof_calls_legacy_mstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test EOF contracts calling Legacy contracts that return data"""
    env = Environment()
    destination_contract_code = Op.MSTORE8(
        0, int.from_bytes(value_returndata_magic, "big")
    ) + Op.RETURN(0, 32)
    destination_contract_address = pre.deploy_contract(destination_contract_code)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
                + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
                + Op.SSTORE(slot_returndata, Op.RETURNDATALOAD(0))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
            )
        ]
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,  # type: ignore
        slot_call_result: value_eof_call_worked,  # type: ignore
        slot_returndatasize: 0x20,  # type: ignore
        slot_returndata: value_returndata_magic
        + b"\0" * (0x20 - len(value_returndata_magic)),  # type: ignore
    }

    if opcode == Op.EXTDELEGATECALL:
        # EOF delegate call to legacy is a light failure by rule
        calling_storage[slot_call_result] = value_eof_call_reverted
        calling_storage[slot_returndatasize] = 0
        calling_storage[slot_returndata] = 0

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage={}),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
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
    "destination_opcode",
    [Op.REVERT, Op.INVALID],
)
@pytest.mark.parametrize("destination_is_eof", [True, False])
def test_eof_calls_revert_abort(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
    destination_opcode: Op,
    destination_is_eof: bool,
):
    """Test EOF contracts calling contracts that revert or abort"""
    env = Environment()

    destination_contract_address = pre.deploy_contract(
        Container.Code(destination_opcode(offset=0, size=0))
        if destination_is_eof
        else destination_opcode(offset=0, size=0)
    )

    caller_contract = Container.Code(
        Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP,
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,
        slot_call_result: value_eof_call_reverted
        if destination_opcode == Op.REVERT
        or (opcode == Op.EXTDELEGATECALL and not destination_is_eof)
        else value_eof_call_failed,
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage={}),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
    ],
)
@pytest.mark.parametrize("fail_opcode", [Op.REVERT, Op.INVALID])
def test_eof_calls_eof_then_fails(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
    fail_opcode: Op,
):
    """Test EOF contracts calling EOF contracts and failing after the call"""
    env = Environment()
    destination_contract_address = pre.deploy_contract(contract_eof_sstore)

    caller_contract = Container.Code(
        Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + fail_opcode(offset=0, size=0),
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    post = {
        calling_contract_address: Account(storage=Storage()),
        destination_contract_address: Account(storage=Storage()),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
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
    "target_account_type",
    (
        "empty",
        "EOA",
        "LegacyContract",
        "EOFContract",
    ),
    ids=lambda x: x,
)
def test_eof_calls_clear_return_buffer(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
    target_account_type: str,
):
    """Test EOF contracts calling clears returndata buffer"""
    env = Environment()
    filling_contract_code = Container.Code(
        Op.MSTORE8(0, int.from_bytes(value_returndata_magic, "big")) + Op.RETURN(0, 32),
    )
    filling_callee_address = pre.deploy_contract(filling_contract_code)

    match target_account_type:
        case "empty":
            target_address = b"\x78" * 20
        case "EOA":
            target_address = pre.fund_eoa()
        case "LegacyContract":
            target_address = pre.deploy_contract(
                code=Op.STOP,
            )
        case "EOFContract":
            target_address = pre.deploy_contract(
                code=Container.Code(Op.STOP),
            )

    caller_contract = Container.Code(
        # First fill the return buffer and sanity check
        Op.EXTCALL(filling_callee_address, 0, 0, 0)
        + Op.SSTORE(slot_returndatasize_before_clear, Op.RETURNDATASIZE)
        # Then call something that doesn't return and check returndata cleared
        + opcode(address=target_address)
        + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP,
    )

    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,
        # Sanity check
        slot_returndatasize_before_clear: 0x20,
        slot_returndatasize: 0,
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
        filling_callee_address: Account(storage={}),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
