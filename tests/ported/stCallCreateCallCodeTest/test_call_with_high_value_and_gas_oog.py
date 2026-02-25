"""
call with value. call takes more gas then tx has, and more value than account has. check returndata.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/callWithHighValueAndGasOOGFiller.json

callee code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x37
    push1 0x00
    mstore8
    push1 0x02
    push1 0x00
    return

contract code:
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push1 0x00
    mstore
    push32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa
    push1 0x20
    mstore
    push1 0x02
    push1 0x00
    push1 0x40
    push1 0x00
    push9 0x056bc75e2d63100000
    push20 0x0896f13e800125c0ccec44f3c434335f0a97bc1b
    push12 0xffffffffffffffffffffffff
    call
    push1 0x00
    sstore
    push1 0x00
    mload
    push1 0x01
    sstore
    ... (1 more instructions)
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
    ["tests/static/state_tests/stCallCreateCallCodeTest/callWithHighValueAndGasOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value",
    [
        100000,
        100000000000000000000,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_call_with_high_value_and_gas_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """call with value. call takes more gas then tx has, and more value than account has. check returndata.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xd187b36e8532efd7f15218fb1781d79330c0cda2")
    contract = Address("0xdfad372452688759edd82c422bf3976eafc89c2b")
    callee = Address("0x0896f13e800125c0ccec44f3c434335f0a97bc1b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x37] + Op.PUSH1[0x0]
        + Op.MSTORE8 + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.RETURN
    ),
    )
    pre[sender] = Account(balance=0x3635c9adc5dea00000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH9[0x56bc75e2d63100000]
        + Op.PUSH20[0x896f13e800125c0ccec44f3c434335f0a97bc1b]
        + Op.PUSH12[0xffffffffffffffffffffffff] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x5},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x897b12d02d588d8a4fe16ff831cbd4459c6f62f8c845b0ccdd31caf068c84a26"
        ),
        to=contract,
        data=b"",
        gas_limit=6000000,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
