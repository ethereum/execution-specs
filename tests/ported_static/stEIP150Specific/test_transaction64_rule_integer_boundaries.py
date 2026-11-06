"""
Danno Ferrin danno.ferrin@gmail.com.

Ported from:
state_tests/stEIP150Specific/Transaction64Rule_integerBoundariesFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stEIP150Specific/Transaction64Rule_integerBoundariesFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "call_gas",
    [
        pytest.param(0x7F, id="int8"),
        pytest.param(0x8F, id="uint8"),
        pytest.param(0x7FFF, id="int16"),
        pytest.param(0x8FFF, id="uint16"),
        pytest.param(0x7FFFFFFF, id="int32"),
        pytest.param(0x8FFFFFFF, id="uint32"),
        pytest.param(0x7FFFFFFFFFFFFFFF, id="int64"),
        pytest.param(0x8FFFFFFFFFFFFFFF, id="uint64"),
        pytest.param(0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, id="int128"),
        pytest.param(0x8FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, id="uint128"),
        pytest.param(
            0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            id="int256",
        ),
        pytest.param(
            0x8FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            id="uint256",
        ),
    ],
)
def test_transaction64_rule_integer_boundaries(
    state_test: StateTestFiller,
    pre: Alloc,
    call_gas: int,
) -> None:
    """
    Call with a gas operand at an integer boundary from each call opcode.

    Each call must succeed with its gas clamped to the 63/64 rule.
    """
    sender = pre.fund_eoa()

    # Source: raw
    # 0x600060FF00
    callee = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0xFF] + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: yul
    # berlin
    # {
    #   let initialgas := gas()
    #   let callgas := calldataload(0)
    #
    #   pop(call(callgas, 0x1000, 0, 0, 0, 0, 0x20))
    #   sstore(0, lt(gas(), initialgas))
    #
    #   pop(callcode(callgas, 0x1000, 0, 0, 0, 0, 0x20))
    #   sstore(1, lt(gas(), initialgas))
    #
    #   pop(delegatecall(callgas, 0x1000, 0, 0x20, 0, 0x20))
    #   sstore(2, lt(gas(), initialgas))
    #
    #   pop(staticcall(callgas, 0x1000, 0, 0x20, 0, 0x20))
    #   sstore(3, lt(gas(), initialgas))
    # }
    gas = Op.CALLDATALOAD(offset=0x0)
    calls = [
        Op.CALL(gas=gas, address=callee, ret_size=0x20),
        Op.CALLCODE(gas=gas, address=callee, ret_size=0x20),
        Op.DELEGATECALL(
            gas=gas, address=callee, args_size=0x20, ret_size=0x20
        ),
        Op.STATICCALL(gas=gas, address=callee, args_size=0x20, ret_size=0x20),
    ]
    code = Op.MSTORE(0x100, Op.GAS)
    for slot, call in enumerate(calls):
        code += Op.SSTORE(slot, call) + Op.SSTORE(
            0x10 + slot, Op.LT(Op.GAS, Op.MLOAD(0x100))
        )
    caller = pre.deploy_contract(code=code, balance=0xBA1A9CE0BA1A9CE)

    tx = Transaction(sender=sender, to=caller, data=Hash(call_gas))

    post = {
        caller: Account(
            storage={
                slot: 1 for i in range(len(calls)) for slot in (i, 0x10 + i)
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)
