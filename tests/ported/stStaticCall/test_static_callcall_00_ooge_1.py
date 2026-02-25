"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcall_00_OOGE_1Filler.json

callee code:
    push1 0x01
    push1 0x02
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x609e4dfe6190235b9a0362084c741d9ec330fb1e
    push3 0x0186a0
    staticcall
    pop
    push1 0x01
    push1 0x20
    mstore
    stop

callee_1 code:
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x1c
    jumpi
    push1 0x01
    extcodesize
    pop
    push1 0x01
    push1 0x80
    mload
    add
    push1 0x80
    mstore
    push1 0x00
    jump
    jumpdest
    ... (1 more instructions)

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x1d401212ba6c32405b4fdc993079acab6c7aab6f
    push3 0x0249f0
    staticcall
    push1 0x00
    sstore
    stop

callee_3 code:
    push1 0x01
    push1 0x02
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xa65f4b36f21ef107a26ab282b736f93d47bf83de
    push3 0x0186a0
    staticcall
    pop
    push1 0x01
    push1 0x20
    mstore
    stop

callee_4 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xa122fc55193a6573fa47c988f537ae631e411058
    push3 0x0249f0
    staticcall
    push1 0x00
    sstore
    stop

callee_5 code:
    push1 0x01
    push1 0x02
    sstore
    callvalue
    push1 0x05
    sstore
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
    ["tests/static/state_tests/stStaticCall/static_callcall_00_OOGE_1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000a2ca69f1cf9ffa7a761899e8dd2f941d40326fd6",
        "000000000000000000000000998a75f1a4457fb7b5872c51f34aa7256f732b1e",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcall_00_ooge_1(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x1d401212ba6c32405b4fdc993079acab6c7aab6f")
    callee_1 = Address("0x609e4dfe6190235b9a0362084c741d9ec330fb1e")
    callee_2 = Address("0x998a75f1a4457fb7b5872c51f34aa7256f732b1e")
    callee_3 = Address("0xa122fc55193a6573fa47c988f537ae631e411058")
    callee_4 = Address("0xa2ca69f1cf9ffa7a761899e8dd2f941d40326fd6")
    callee_5 = Address("0xa65f4b36f21ef107a26ab282b736f93d47bf83de")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x609e4dfe6190235b9a0362084c741d9ec330fb1e] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x1c] + Op.JUMPI + Op.PUSH1[0x1] + Op.EXTCODESIZE
        + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1d401212ba6c32405b4fdc993079acab6c7aab6f] + Op.PUSH3[0x249f0]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa65f4b36f21ef107a26ab282b736f93d47bf83de] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa122fc55193a6573fa47c988f537ae631e411058] + Op.PUSH3[0x249f0]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SSTORE + Op.CALLVALUE + Op.PUSH1[0x5]
        + Op.SSTORE + Op.STOP
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
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=380066,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
