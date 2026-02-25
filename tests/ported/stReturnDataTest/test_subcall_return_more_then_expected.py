"""
https://github.com/ethereum/tests/issues/558 (subcall/opcode return more data then expected)

Ported from:
tests/static/state_tests/stReturnDataTest/subcallReturnMoreThenExpectedFiller.yml

callee code:
    push32 0x1122334455667788991011121314151617181920212223242526272829303132
    push1 0x00
    mstore
    push32 0x3334353637383940414243444546474849505152535455565758596061626364
    push1 0x20
    mstore
    push1 0x40
    push1 0x00
    revert
    stop

callee_1 code:
    push32 0x1122334455667788991011121314151617181920212223242526272829303132
    push1 0x00
    mstore
    push32 0x3334353637383940414243444546474849505152535455565758596061626364
    push1 0x20
    mstore
    push1 0x40
    push1 0x00
    return
    stop

contract code:
    push1 0x0c
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xa8592f39b32943f9f464090497722b4f9c15f598
    push3 0x030d40
    call
    pop
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    mstore
    push1 0x0c
    push1 0x00
    push1 0x00
    push1 0x00
    ... (102 more instructions)
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stReturnDataTest/subcallReturnMoreThenExpectedFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_subcall_return_more_then_expected(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """https://github.com/ethereum/tests/issues/558 (subcall/opcode return more data then expected)."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xca70835d5e9b8c8e139a9693ab05705d291f86bb")
    callee = Address("0x028cdafc3d5d27d006ffb88e1ecf2fa4b412ee4f")
    callee_1 = Address("0xa8592f39b32943f9f464090497722b4f9c15f598")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH32[0x1122334455667788991011121314151617181920212223242526272829303132]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0x3334353637383940414243444546474849505152535455565758596061626364]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.REVERT
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH32[0x1122334455667788991011121314151617181920212223242526272829303132]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0x3334353637383940414243444546474849505152535455565758596061626364]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0xc] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xa8592f39b32943f9f464090497722b4f9c15f598]
        + Op.PUSH3[0x30d40] + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa8592f39b32943f9f464090497722b4f9c15f598] + Op.PUSH3[0x30d40]
        + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa8592f39b32943f9f464090497722b4f9c15f598] + Op.PUSH3[0x30d40]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa8592f39b32943f9f464090497722b4f9c15f598] + Op.PUSH3[0x30d40]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x28cdafc3d5d27d006ffb88e1ecf2fa4b412ee4f] + Op.PUSH3[0x30d40]
        + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x4] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x28cdafc3d5d27d006ffb88e1ecf2fa4b412ee4f] + Op.PUSH3[0x30d40]
        + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x5]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x28cdafc3d5d27d006ffb88e1ecf2fa4b412ee4f] + Op.PUSH3[0x30d40]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x6]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x28cdafc3d5d27d006ffb88e1ecf2fa4b412ee4f] + Op.PUSH3[0x30d40]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x7] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
