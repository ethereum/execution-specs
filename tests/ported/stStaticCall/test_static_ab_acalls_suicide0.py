"""
Ported from:
tests/static/state_tests/stStaticCall/static_ABAcallsSuicide0Filler.json

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x644ac2b24a9316ed4c55001e5eda02d77f729c7b
    push3 0x0186a0
    staticcall
    pc
    mstore
    push20 0xc20b4779ed25a1ccf1848f1cbcc84433fcb9d083
    selfdestruct
    stop

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xc20b4779ed25a1ccf1848f1cbcc84433fcb9d083
    push3 0x0186a0
    staticcall
    pc
    sstore
    push20 0xc20b4779ed25a1ccf1848f1cbcc84433fcb9d083
    selfdestruct
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x15631f76b02193e5716cbd4b4d696f2f7a39f0a4
    push2 0xc350
    staticcall
    push1 0x01
    add
    pc
    mstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    callvalue
    push1 0x00
    calldataload
    gas
    call
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_3 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x195198c66c5e31767d41365ff8003c5fe4387110
    push2 0xc350
    staticcall
    push1 0x01
    add
    pc
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
    ["tests/static/state_tests/stStaticCall/static_ABAcallsSuicide0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000195198c66c5e31767d41365ff8003c5fe4387110",
        "00000000000000000000000015631f76b02193e5716cbd4b4d696f2f7a39f0a4",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_ab_acalls_suicide0(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x15631f76b02193e5716cbd4b4d696f2f7a39f0a4")
    callee_1 = Address("0x195198c66c5e31767d41365ff8003c5fe4387110")
    callee_2 = Address("0x644ac2b24a9316ed4c55001e5eda02d77f729c7b")
    callee_3 = Address("0xc20b4779ed25a1ccf1848f1cbcc84433fcb9d083")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x644ac2b24a9316ed4c55001e5eda02d77f729c7b] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.PC + Op.MSTORE
        + Op.PUSH20[0xc20b4779ed25a1ccf1848f1cbcc84433fcb9d083] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc20b4779ed25a1ccf1848f1cbcc84433fcb9d083] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.PC + Op.SSTORE
        + Op.PUSH20[0xc20b4779ed25a1ccf1848f1cbcc84433fcb9d083] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x15631f76b02193e5716cbd4b4d696f2f7a39f0a4] + Op.PUSH2[0xc350]
        + Op.STATICCALL + Op.PUSH1[0x1] + Op.ADD + Op.PC + Op.MSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x195198c66c5e31767d41365ff8003c5fe4387110] + Op.PUSH2[0xc350]
        + Op.STATICCALL + Op.PUSH1[0x1] + Op.ADD + Op.PC + Op.SSTORE + Op.STOP
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
        gas_limit=10000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
