"""
https://github.com/ethereum/tests/issues/652

Ported from:
tests/static/state_tests/stExtCodeHash/callToNonExistentFiller.json

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xdead000000000000000000000000000000000001
    push2 0x61a8
    call
    push1 0x00
    sstore
    push20 0xdead000000000000000000000000000000000001
    extcodehash
    push1 0x01
    sstore
    stop

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    gas
    callcode
    stop

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xdead000000000000000000000000000000000001
    push2 0x61a8
    callcode
    push1 0x00
    sstore
    push20 0xdead000000000000000000000000000000000001
    extcodehash
    push1 0x01
    sstore
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xdead000000000000000000000000000000000001
    push2 0x61a8
    delegatecall
    push1 0x00
    sstore
    push20 0xdead000000000000000000000000000000000001
    extcodehash
    push1 0x01
    sstore
    stop

callee_3 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xdead000000000000000000000000000000000001
    push2 0x61a8
    staticcall
    push1 0x00
    sstore
    push20 0xdead000000000000000000000000000000000001
    extcodehash
    push1 0x01
    sstore
    stop
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
    ["tests/static/state_tests/stExtCodeHash/callToNonExistentFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "00000000000000000000000005705e771b914ec6992c8b6dfdfecd9f51e9dbbd",
        "000000000000000000000000920c5d2db11d6459c77c03242ab3e1307e0e72c3",
        "000000000000000000000000c11aae23923ca74760be6b1120a21d013c504faf",
        "000000000000000000000000c62f6d22c52dd165f9ef2c2b8daacf1b87b924b7",
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_call_to_non_existent(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """https://github.com/ethereum/tests/issues/652."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x0643600618f0ae5095b4bda2e0f11a79e6d2d541")
    callee = Address("0x05705e771b914ec6992c8b6dfdfecd9f51e9dbbd")
    callee_1 = Address("0x920c5d2db11d6459c77c03242ab3e1307e0e72c3")
    callee_2 = Address("0xc11aae23923ca74760be6b1120a21d013c504faf")
    callee_3 = Address("0xc62f6d22c52dd165f9ef2c2b8daacf1b87b924b7")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdead000000000000000000000000000000000001]
        + Op.PUSH2[0x61a8] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH20[0xdead000000000000000000000000000000000001] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALLCODE
        + Op.STOP
    ),
        storage={0x1: 0x1122},
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdead000000000000000000000000000000000001]
        + Op.PUSH2[0x61a8] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH20[0xdead000000000000000000000000000000000001] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xdead000000000000000000000000000000000001] + Op.PUSH2[0x61a8]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH20[0xdead000000000000000000000000000000000001] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xdead000000000000000000000000000000000001] + Op.PUSH2[0x61a8]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH20[0xdead000000000000000000000000000000000001] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
