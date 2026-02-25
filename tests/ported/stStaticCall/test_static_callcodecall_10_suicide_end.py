"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcodecall_10_SuicideEndFiller.json

callee code:
    push1 0x01
    push1 0x02
    sstore
    stop

contract code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xdc07fff80d888eba04eab962d37897f6c923462b
    push3 0x0249f0
    delegatecall
    push1 0x00
    sstore
    gas
    push1 0x01
    sstore
    stop

callee_1 code:
    push1 0x01
    push1 0x02
    mstore
    stop

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    calldataload
    push2 0xc350
    staticcall
    pop
    push20 0x99b0d2d9eea3205f4de64fdc26910432824ab1a7
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
    ["tests/static/state_tests/stStaticCall/static_callcodecall_10_SuicideEndFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000cfb5784a5e49924becc2d5c5d2ee0a9b141e6216",
        "000000000000000000000000703b936fd4d674f0ff5d6957f61097152f8781b8",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcodecall_10_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x99b0d2d9eea3205f4de64fdc26910432824ab1a7")
    callee = Address("0x703b936fd4d674f0ff5d6957f61097152f8781b8")
    callee_1 = Address("0xcfb5784a5e49924becc2d5c5d2ee0a9b141e6216")
    callee_2 = Address("0xdc07fff80d888eba04eab962d37897f6c923462b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0x2540be400,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP,
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xdc07fff80d888eba04eab962d37897f6c923462b] + Op.PUSH3[0x249f0]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2540be400,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH2[0xc350] + Op.STATICCALL + Op.POP
        + Op.PUSH20[0x99b0d2d9eea3205f4de64fdc26910432824ab1a7] + Op.SELFDESTRUCT
        + Op.STOP
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
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
