"""
Ported from:
tests/static/state_tests/stStaticCall/static_ABAcallsSuicide1Filler.json

contract code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push20 0x945304eb96065b2a98b57a48a06ae28d285a71b5
    push1 0x00
    calldataload
    staticcall
    stop

callee code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push20 0x095e7baea6a6c7c4c2dfeb977efac326af552d87
    push2 0xc350
    push1 0x00
    calldataload
    sub
    staticcall
    pop
    push20 0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6
    selfdestruct
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
    ["tests/static/state_tests/stStaticCall/static_ABAcallsSuicide1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "00000000000000000000000000000000000000000000000000000000000186a0",
        "00000000000000000000000000000000000000000000000000000000000486a0",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_ab_acalls_suicide1(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    callee = Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH20[0x945304eb96065b2a98b57a48a06ae28d285a71b5] + Op.PUSH1[0x0]
        + Op.CALLDATALOAD + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH20[0x95e7baea6a6c7c4c2dfeb977efac326af552d87] + Op.PUSH2[0xc350]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SUB + Op.STATICCALL + Op.POP
        + Op.PUSH20[0xf572e5295c57f15886f9b263e2f6d2d6c7b5ec6] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=10000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
