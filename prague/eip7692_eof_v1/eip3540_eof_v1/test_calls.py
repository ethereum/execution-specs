"""
test calls across EOF and Legacy
"""
import itertools

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    StateTestFiller,
    Storage,
    TestAddress,
    Transaction,
)
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import NON_RETURNING_SECTION
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
slot_last_slot = next(_slot)

"""Storage values for common testing fields"""
value_code_worked = 0x2015
value_legacy_call_worked = 1
value_legacy_call_failed = 0
value_eof_call_worked = 0
value_eof_call_failed = 1
value_eof_call_reverted = 2
value_returndata_magic = b"\x42"


contract_eof_sstore = Container(
    sections=[
        Section.Code(
            code=Op.SSTORE(slot_caller, Op.CALLER()) + Op.STOP,
            code_outputs=NON_RETURNING_SECTION,
            max_stack_height=2,
        )
    ]
)


@pytest.mark.parametrize(
    ["opcode", "suffix"],
    [
        [Op.CALL, [0, 0, 0, 0, 0]],
        [Op.DELEGATECALL, [0, 0, 0, 0]],
        [Op.CALLCODE, [0, 0, 0, 0, 0]],
        [Op.STATICCALL, [0, 0, 0, 0]],
    ],
    ids=["call", "delegatecall", "callcode", "staticall"],
)
def test_legacy_calls_eof_sstore(
    state_test: StateTestFiller,
    opcode: Op,
    suffix: list[int],
):
    """Test legacy contracts calling EOF contracts that use SSTORE"""
    env = Environment()
    calling_contract_address = Address(0x1000000)
    destination_contract_address = Address(0x1000001)

    caller_contract = Op.SSTORE(
        slot_call_result, opcode(Op.GAS, destination_contract_address, *suffix)
    ) + Op.SSTORE(slot_code_worked, value_code_worked)

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        calling_contract_address: Account(
            code=caller_contract,
            nonce=1,
        ),
        destination_contract_address: Account(
            code=contract_eof_sstore,
            nonce=1,
        ),
    }

    tx = Transaction(
        nonce=1,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        gas_price=10,
        protected=False,
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
        calling_storage[slot_caller] = TestAddress
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
    ["opcode", "suffix"],
    [
        [Op.CALL, [0, 0, 0, 0, 0]],
        [Op.DELEGATECALL, [0, 0, 0, 0]],
        [Op.CALLCODE, [0, 0, 0, 0, 0]],
        [Op.STATICCALL, [0, 0, 0, 0]],
    ],
    ids=["call", "delegatecall", "callcode", "staticall"],
)
def test_legacy_calls_eof_mstore(
    state_test: StateTestFiller,
    opcode: Op,
    suffix: list[int],
):
    """Test legacy contracts calling EOF contracts that only return data"""
    env = Environment()
    calling_contract_address = Address(0x1000000)
    destination_contract_address = Address(0x1000001)

    caller_contract = (
        Op.SSTORE(slot_call_result, opcode(Op.GAS, destination_contract_address, *suffix))
        + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(31, 0, 1)
        + Op.SSTORE(slot_returndata, Op.MLOAD(0))
        + Op.SSTORE(slot_code_worked, value_code_worked)
    )

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        calling_contract_address: Account(
            code=caller_contract,
            nonce=1,
        ),
        destination_contract_address: Account(
            code=Container(
                sections=[
                    Section.Code(
                        code=Op.MSTORE8(0, int.from_bytes(value_returndata_magic, "big"))
                        + Op.RETURN(0, len(value_returndata_magic)),
                        code_outputs=NON_RETURNING_SECTION,
                        max_stack_height=2,
                    )
                ]
            ),
            nonce=1,
        ),
    }

    tx = Transaction(
        nonce=1,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        gas_price=10,
        protected=False,
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
    ["opcode", "suffix"],
    [
        [Op.EXTCALL, [0, 0, 0]],
        [Op.EXTDELEGATECALL, [0, 0]],
        [Op.EXTSTATICCALL, [0, 0]],
    ],
    ids=["extcall", "extdelegatecall", "extstaticall"],
)
def test_eof_calls_eof_sstore(
    state_test: StateTestFiller,
    opcode: Op,
    suffix: list[int],
):
    """Test EOF contracts calling EOF contracts that use SSTORE"""
    env = Environment()
    calling_contract_address = Address(0x1000000)
    destination_contract_address = Address(0x1000001)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(destination_contract_address, *suffix))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1 + len(suffix),
            )
        ]
    )

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        calling_contract_address: Account(
            code=caller_contract,
            nonce=1,
        ),
        destination_contract_address: Account(
            code=contract_eof_sstore,
            nonce=1,
        ),
    }

    tx = Transaction(
        nonce=1,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        gas_price=10,
        protected=False,
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
        calling_storage[slot_caller] = TestAddress
    elif opcode == Op.EXTSTATICCALL:
        calling_storage[slot_call_result] = value_eof_call_reverted

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
    ["opcode", "suffix"],
    [
        [Op.EXTCALL, [0, 0, 0]],
        [Op.EXTDELEGATECALL, [0, 0]],
        [Op.EXTSTATICCALL, [0, 0]],
    ],
    ids=["extcall", "extdelegatecall", "extstaticall"],
)
def test_eof_calls_eof_mstore(
    state_test: StateTestFiller,
    opcode: Op,
    suffix: list[int],
):
    """Test EOF contracts calling EOF contracts that return data"""
    env = Environment()
    calling_contract_address = Address(0x1000000)
    destination_contract_address = Address(0x1000001)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(destination_contract_address, *suffix))
                + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
                + Op.SSTORE(slot_returndata, Op.RETURNDATALOAD(0))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1 + len(suffix),
            )
        ]
    )

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        calling_contract_address: Account(
            code=caller_contract,
            nonce=1,
        ),
        destination_contract_address: Account(
            code=Container(
                sections=[
                    Section.Code(
                        code=Op.MSTORE8(0, int.from_bytes(value_returndata_magic, "big"))
                        + Op.RETURN(0, 32),
                        code_outputs=NON_RETURNING_SECTION,
                        max_stack_height=2,
                    )
                ]
            ),
            nonce=1,
        ),
    }

    tx = Transaction(
        nonce=1,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        gas_price=10,
        protected=False,
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
    ["opcode", "suffix"],
    [
        [Op.EXTCALL, [0, 0, 0]],
        [Op.EXTDELEGATECALL, [0, 0]],
        [Op.EXTSTATICCALL, [0, 0]],
    ],
    ids=["extcall", "extdelegatecall", "extstaticall"],
)
def test_eof_calls_legacy_sstore(
    state_test: StateTestFiller,
    opcode: Op,
    suffix: list[int],
):
    """Test EOF contracts calling Legacy contracts that use SSTORE"""
    env = Environment()
    calling_contract_address = Address(0x1000000)
    destination_contract_address = Address(0x1000001)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(destination_contract_address, *suffix))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1 + len(suffix),
            )
        ]
    )

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        calling_contract_address: Account(
            code=caller_contract,
            nonce=1,
        ),
        destination_contract_address: Account(
            code=Op.SSTORE(slot_caller, Op.CALLER()) + Op.STOP,
            nonce=1,
        ),
    }

    tx = Transaction(
        nonce=1,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        gas_price=10,
        protected=False,
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
        # EOF delegate call to legacy is a failure by rule
        calling_storage[slot_call_result] = value_eof_call_failed
    elif opcode == Op.EXTSTATICCALL:
        calling_storage[slot_call_result] = value_eof_call_reverted

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
    ["opcode", "suffix"],
    [
        [Op.EXTCALL, [0, 0, 0]],
        [Op.EXTDELEGATECALL, [0, 0]],
        [Op.EXTSTATICCALL, [0, 0]],
    ],
    ids=["extcall", "extdelegatecall", "extstaticall"],
)
def test_eof_calls_legacy_mstore(
    state_test: StateTestFiller,
    opcode: Op,
    suffix: list[int],
):
    """Test EOF contracts calling Legacy contracts that return data"""
    env = Environment()
    calling_contract_address = Address(0x1000000)
    destination_contract_address = Address(0x1000001)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(destination_contract_address, *suffix))
                + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
                + Op.SSTORE(slot_returndata, Op.RETURNDATALOAD(0))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=1 + len(suffix),
            )
        ]
    )

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        calling_contract_address: Account(
            code=caller_contract,
            nonce=1,
        ),
        destination_contract_address: Account(
            code=Op.MSTORE8(0, int.from_bytes(value_returndata_magic, "big")) + Op.RETURN(0, 32),
            nonce=1,
        ),
    }

    tx = Transaction(
        nonce=1,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        gas_price=10,
        protected=False,
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
        # EOF delegate call to legacy is a failure by rule
        calling_storage[slot_call_result] = value_eof_call_failed
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
