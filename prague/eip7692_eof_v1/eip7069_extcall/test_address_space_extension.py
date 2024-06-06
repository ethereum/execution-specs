"""
Tests the "Address Space Extension" aspect of EXT*CALL
"""
import itertools

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    StateTestFiller,
    TestAddress,
    Transaction,
)
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from .spec import CALL_SUCCESS, EXTCALL_REVERT, EXTCALL_SUCCESS

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7069.md"
REFERENCE_SPEC_VERSION = "1795943aeacc86131d5ab6bb3d65824b3b1d4cad"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

_address_allocation = itertools.count(0x10000)
address_entry_point = Address(next(_address_allocation))
address_caller = Address(next(_address_allocation))

_slot = itertools.count(1)
slot_top_level_call_status = next(_slot)
slot_target_call_status = next(_slot)
slot_target_returndata = next(_slot)

value_exceptional_abort_canary = 0x1984


@pytest.mark.parametrize(
    "target_address",
    (
        pytest.param(b"", id="zero"),
        pytest.param(b"\xc0\xde", id="short"),
        pytest.param(b"\x78" * 20, id="mid_20"),
        pytest.param(b"\xff" * 20, id="max_20"),
        pytest.param(b"\x01" + (b"\x00" * 20), id="min_ase"),
        pytest.param(b"\x5a" * 28, id="mid_ase"),
        pytest.param(b"\x5a" * 32, id="full_ase"),
        pytest.param(b"\xff" * 32, id="max_ase"),
    ),
)
@pytest.mark.parametrize(
    "target_account_type", ("empty", "EOA", "LegacyContract", "EOFContract"), ids=lambda x: x
)
@pytest.mark.parametrize(
    "target_opcode",
    (
        Op.CALL,
        Op.CALLCODE,
        Op.STATICCALL,
        Op.DELEGATECALL,
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ),
)
def test_address_space_extension(
    state_test: StateTestFiller,
    target_address: bytes,
    target_opcode: Op,
    target_account_type: str,
):
    """
    Test contacts with possibly extended address and fail if address is too large
    """
    env = Environment()

    ase_address = len(target_address) > 20
    stripped_address = target_address[-20:] if ase_address else target_address
    if ase_address and target_address[0] == b"00":
        raise ValueError("Test instrumentation requires target addresses trim leading zeros")

    match target_opcode:
        case Op.CALL | Op.CALLCODE:
            call_suffix = [0, 0, 0, 0, 0]
            ase_ready_opcode = False
        case Op.DELEGATECALL | Op.STATICCALL:
            call_suffix = [0, 0, 0, 0]
            ase_ready_opcode = False
        case Op.EXTCALL:
            call_suffix = [0, 0, 0]
            ase_ready_opcode = True
        case Op.EXTDELEGATECALL | Op.EXTSTATICCALL:
            call_suffix = [0, 0]
            ase_ready_opcode = True
        case _:
            raise ValueError("Unexpected opcode ", target_opcode)

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        address_entry_point: Account(
            code=(
                Op.MSTORE(0, Op.PUSH32(target_address))
                + Op.SSTORE(
                    slot_top_level_call_status,
                    Op.CALL(50000, address_caller, 0, 0, 32, 0, 0),
                )
                + Op.STOP()
            ),
            nonce=1,
            storage={
                slot_top_level_call_status: value_exceptional_abort_canary,
            },
        ),
        address_caller: Account(
            code=Container(
                sections=[
                    Section.Code(
                        code=Op.SSTORE(
                            slot_target_call_status,
                            target_opcode(Op.CALLDATALOAD(0), *call_suffix),
                        )
                        + Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE)
                        + Op.SSTORE(slot_target_returndata, Op.MLOAD(0))
                        + Op.STOP,
                        code_inputs=0,
                        max_stack_height=1 + len(call_suffix),
                    )
                ],
            )
            if ase_ready_opcode
            else Op.SSTORE(
                slot_target_call_status,
                target_opcode(Op.GAS, Op.CALLDATALOAD(0), *call_suffix),
            )
            + Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE)
            + Op.SSTORE(slot_target_returndata, Op.MLOAD(0))
            + Op.STOP,
            nonce=1,
            storage={
                slot_target_call_status: value_exceptional_abort_canary,
                slot_target_returndata: value_exceptional_abort_canary,
            },
        ),
    }
    match target_account_type:
        case "empty":
            # add no account
            pass
        case "EOA":
            pre[Address(stripped_address)] = Account(code="", balance=10**18, nonce=9)
        case "LegacyContract":
            pre[Address(stripped_address)] = Account(
                code=Op.MSTORE(0, Op.ADDRESS) + Op.RETURN(0, 32),
                balance=0,
                nonce=0,
            )
        case "EOFContract":
            pre[Address(stripped_address)] = Account(
                code=Container(
                    sections=[
                        Section.Code(
                            code=Op.MSTORE(0, Op.ADDRESS) + Op.RETURN(0, 32),
                            max_stack_height=2,
                        )
                    ],
                ),
                balance=0,
                nonce=0,
            )

    caller_storage: dict[int, int | bytes | Address] = {}
    match target_account_type:
        case "empty" | "EOA":
            if ase_address and ase_ready_opcode:
                caller_storage[slot_target_call_status] = value_exceptional_abort_canary
                caller_storage[slot_target_returndata] = value_exceptional_abort_canary
            elif target_opcode == Op.EXTDELEGATECALL:
                caller_storage[slot_target_call_status] = EXTCALL_REVERT
                caller_storage[slot_target_returndata] = 0
            else:
                caller_storage[slot_target_call_status] = (
                    EXTCALL_SUCCESS if ase_ready_opcode else CALL_SUCCESS
                )
        case "LegacyContract" | "EOFContract":
            match target_opcode:
                case Op.CALL | Op.STATICCALL:
                    caller_storage[slot_target_call_status] = CALL_SUCCESS
                    # CALL and STATICCALL call will call the stripped address
                    caller_storage[slot_target_returndata] = stripped_address
                case Op.CALLCODE | Op.DELEGATECALL:
                    caller_storage[slot_target_call_status] = CALL_SUCCESS
                    # CALLCODE and DELEGATECALL call will call the stripped address
                    # but will change the sender to self
                    caller_storage[slot_target_returndata] = address_caller
                case Op.EXTCALL | Op.EXTSTATICCALL:
                    # EXTCALL and EXTSTATICCALL will fault if calling an ASE address
                    if ase_address:
                        caller_storage[slot_target_call_status] = value_exceptional_abort_canary
                        caller_storage[slot_target_returndata] = value_exceptional_abort_canary
                    else:
                        caller_storage[slot_target_call_status] = EXTCALL_SUCCESS
                        caller_storage[slot_target_returndata] = stripped_address
                case Op.EXTDELEGATECALL:
                    if ase_address:
                        caller_storage[slot_target_call_status] = value_exceptional_abort_canary
                        caller_storage[slot_target_returndata] = value_exceptional_abort_canary
                    elif target_account_type == "LegacyContract":
                        caller_storage[slot_target_call_status] = EXTCALL_REVERT
                        caller_storage[slot_target_returndata] = 0
                    else:
                        caller_storage[slot_target_call_status] = EXTCALL_SUCCESS
                        # EXTDELEGATECALL call will call the stripped address
                        # but will change the sender to self
                        caller_storage[slot_target_returndata] = address_caller

    post = {
        address_entry_point: Account(
            storage={
                slot_top_level_call_status: EXTCALL_SUCCESS
                if ase_ready_opcode and ase_address
                else CALL_SUCCESS
            }
        ),
        address_caller: Account(storage=caller_storage),
    }

    tx = Transaction(
        nonce=1,
        to=address_entry_point,
        gas_limit=50000000,
        gas_price=10,
        protected=False,
        data="",
    )

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
