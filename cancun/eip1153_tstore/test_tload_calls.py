"""
Ethereum Transient Storage EIP Tests
https://eips.ethereum.org/EIPS/eip-1153.
"""

import pytest

from ethereum_test_tools import Account, Address, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.vm.opcode import Bytecode
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-1153.md"
REFERENCE_SPEC_VERSION = "1eb863b534a5a3e19e9c196ab2a7f3db4bb9da17"


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("call_type", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL])
def test_tload_calls(state_test: StateTestFiller, pre: Alloc, call_type: Op):
    """
    Ported .json vectors.

    (04_tloadAfterCallFiller.yml)
    Loading a slot after a call to another contract is 0.

    (12_tloadDelegateCallFiller.yml)
    delegatecall reads transient storage in the context of the current address
    """
    # Storage variables
    slot_a_tload_after_subcall_result = 0
    slot_a_subcall_result = 1
    slot_b_subcall_tload_result = 2
    slot_b_subcall_updated_tload_result = 3

    def make_call(call_type: Op, address: Address) -> Bytecode:
        if call_type == Op.DELEGATECALL or call_type == Op.STATICCALL:
            return call_type(Op.GAS(), address, 0, 32, 0, 0)
        else:
            return call_type(Op.GAS(), address, 0, 0, 32, 0, 0)

    address_call = pre.deploy_contract(
        balance=1_000_000_000_000_000_000,
        code=Op.JUMPDEST()
        + Op.SSTORE(slot_b_subcall_tload_result, Op.TLOAD(0))
        + Op.TSTORE(0, 20)
        + Op.SSTORE(slot_b_subcall_updated_tload_result, Op.TLOAD(0)),
        storage={
            slot_b_subcall_tload_result: 0xFF,
            slot_b_subcall_updated_tload_result: 0xFF,
        },
    )

    address_to = pre.deploy_contract(
        balance=1_000_000_000_000_000_000,
        code=Op.JUMPDEST()
        + Op.TSTORE(0, 10)
        + Op.SSTORE(slot_a_subcall_result, make_call(call_type, address_call))
        + Op.SSTORE(slot_a_tload_after_subcall_result, Op.TLOAD(0)),
        storage={
            slot_a_subcall_result: 0xFF,
            slot_a_tload_after_subcall_result: 0xFF,
        },
    )

    post = {
        address_to: Account(
            storage={
                # other calls don't change context, there for tload updated in this account
                slot_a_tload_after_subcall_result: 10 if call_type == Op.CALL else 20,
                slot_a_subcall_result: 1,
                # since context unchanged the subcall works as if continued execution
                slot_b_subcall_tload_result: 0 if call_type == Op.CALL else 10,
                slot_b_subcall_updated_tload_result: 0 if call_type == Op.CALL else 20,
            }
        ),
        address_call: Account(
            storage={
                slot_b_subcall_tload_result: 0 if call_type == Op.CALL else 0xFF,
                slot_b_subcall_updated_tload_result: 20 if call_type == Op.CALL else 0xFF,
            }
        ),
    }

    tx = Transaction(
        sender=pre.fund_eoa(7_000_000_000_000_000_000),
        to=address_to,
        gas_price=10,
        data=b"",
        gas_limit=5000000,
        value=0,
    )

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
