"""
Ethereum Transient Storage EIP Tests
https://eips.ethereum.org/EIPS/eip-1153.
"""

from enum import Enum

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Case,
    Environment,
    Hash,
    StateTestFiller,
    Switch,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Bytecode
from ethereum_test_tools.vm.opcode import Macros as Om
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-1153.md"
REFERENCE_SPEC_VERSION = "1eb863b534a5a3e19e9c196ab2a7f3db4bb9da17"


class CallDestType(Enum):
    """Call dest type."""

    REENTRANCY = 1
    EXTERNAL_CALL = 2


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("call_type", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL])
@pytest.mark.parametrize("call_return", [Op.RETURN, Op.REVERT, Om.OOG])
@pytest.mark.parametrize("call_dest_type", [CallDestType.REENTRANCY, CallDestType.EXTERNAL_CALL])
def test_tstore_reentrancy(
    state_test: StateTestFiller,
    pre: Alloc,
    call_type: Op,
    call_return: Op,
    call_dest_type: CallDestType,
):
    """
    Ported .json vectors.

    (06_tstoreInReentrancyCallFiller.yml)
    Reentrant calls access the same transient storage

    (07_tloadAfterReentrancyStoreFiller.yml)
    Successfully returned calls do not revert transient storage writes

    (08_revertUndoesTransientStoreFiller.yml)
    Revert undoes the transient storage writes from a call.

    (09_revertUndoesAllFiller.yml)
    Revert undoes all the transient storage writes to the same key from the failed call.

    (11_tstoreDelegateCallFiller.yml)
    delegatecall manipulates transient storage in the context of the current address.

    (13_tloadStaticCallFiller.yml)
    Transient storage cannot be manipulated in a static context, tstore reverts

    (20_oogUndoesTransientStoreInCallFiller.yml)
    Out of gas undoes the transient storage writes from a call.
    """
    tload_value_set_before_call = 80
    tload_value_set_in_call = 90

    # Storage cells
    slot_tload_before_call = 0
    slot_tload_in_subcall_result = 1
    slot_tload_after_call = 2
    slot_subcall_worked = 3
    slot_tload_1_after_call = 4
    slot_tstore_overwrite = 5
    slot_code_worked = 6

    # Function names
    do_tstore = 1
    do_reenter = 2
    call_dest_address: Bytecode | Address
    call_dest_address = Op.ADDRESS()

    def make_call(call_type: Op) -> Bytecode:
        if call_type == Op.DELEGATECALL or call_type == Op.STATICCALL:
            return call_type(Op.GAS(), call_dest_address, 0, 32, 32, 32)
        else:
            return call_type(Op.GAS(), call_dest_address, 0, 0, 32, 32, 32)

    subcall_code = (
        Op.TSTORE(0, 89)
        + Op.TSTORE(0, tload_value_set_in_call)
        + Op.TSTORE(1, 11)
        + Op.TSTORE(1, 12)
        + Op.MSTORE(0, Op.TLOAD(0))
        + call_return(0, 32)
    )

    address_code = pre.deploy_contract(
        balance=0,
        code=subcall_code,
        storage={},
    )
    if call_dest_type == CallDestType.EXTERNAL_CALL:
        call_dest_address = address_code

    address_to = pre.deploy_contract(
        balance=1_000_000_000_000_000_000,
        code=Switch(
            cases=[
                Case(
                    condition=Op.EQ(Op.CALLDATALOAD(0), do_tstore),
                    action=subcall_code,
                ),
                Case(
                    condition=Op.EQ(Op.CALLDATALOAD(0), do_reenter),
                    action=Op.TSTORE(0, tload_value_set_before_call)
                    + Op.SSTORE(slot_tload_before_call, Op.TLOAD(0))
                    + Op.MSTORE(0, do_tstore)
                    + Op.MSTORE(32, 0xFF)
                    + Op.SSTORE(slot_subcall_worked, make_call(call_type))
                    + Op.SSTORE(slot_tload_in_subcall_result, Op.MLOAD(32))
                    + Op.SSTORE(slot_tload_after_call, Op.TLOAD(0))
                    + Op.SSTORE(slot_tload_1_after_call, Op.TLOAD(1))
                    + Op.TSTORE(0, 50)
                    + Op.SSTORE(slot_tstore_overwrite, Op.TLOAD(0))
                    + Op.SSTORE(slot_code_worked, 1),
                ),
            ],
            default_action=None,
        ),
        storage={
            slot_tload_before_call: 0xFF,
            slot_tload_in_subcall_result: 0xFF,
            slot_tload_after_call: 0xFF,
            slot_subcall_worked: 0xFF,
            slot_tload_1_after_call: 0xFF,
            slot_tstore_overwrite: 0xFF,
            slot_code_worked: 0xFF,
        },
    )

    on_failing_calls = call_type == Op.STATICCALL or call_return in [Op.REVERT, Om.OOG]
    on_successful_delegate_or_callcode = call_type in [
        Op.DELEGATECALL,
        Op.CALLCODE,
    ] and call_return not in [Op.REVERT, Om.OOG]

    if call_dest_type == CallDestType.REENTRANCY:
        post = {
            address_to: Account(
                storage={
                    slot_code_worked: 1,
                    slot_tload_before_call: tload_value_set_before_call,
                    slot_tload_in_subcall_result: (
                        # we fail to obtain in call result if it fails
                        0xFF
                        if call_type == Op.STATICCALL or call_return == Om.OOG
                        else tload_value_set_in_call
                    ),
                    # reentrant tstore overrides value in upper level
                    slot_tload_after_call: (
                        tload_value_set_before_call
                        if on_failing_calls
                        else tload_value_set_in_call
                    ),
                    slot_tload_1_after_call: 0 if on_failing_calls else 12,
                    slot_tstore_overwrite: 50,
                    # tstore in static call not allowed
                    slot_subcall_worked: 0 if on_failing_calls else 1,
                }
            )
        }
    else:
        post = {
            address_to: Account(
                storage={
                    slot_code_worked: 1,
                    slot_tload_before_call: tload_value_set_before_call,
                    slot_tload_in_subcall_result: (
                        # we fail to obtain in call result if it fails
                        0xFF
                        if call_type == Op.STATICCALL or call_return == Om.OOG
                        else tload_value_set_in_call
                    ),
                    # external tstore overrides value in upper level only in delegate and callcode
                    slot_tload_after_call: (
                        tload_value_set_in_call
                        if on_successful_delegate_or_callcode
                        else tload_value_set_before_call
                    ),
                    slot_tload_1_after_call: 12 if on_successful_delegate_or_callcode else 0,
                    slot_tstore_overwrite: 50,
                    # tstore in static call not allowed, reentrancy means external call here
                    slot_subcall_worked: 0 if on_failing_calls else 1,
                }
            )
        }

    tx = Transaction(
        sender=pre.fund_eoa(7_000_000_000_000_000_000),
        to=address_to,
        gas_price=10,
        data=Hash(do_reenter),
        gas_limit=5000000,
        value=0,
    )

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
