"""
Ported from:
tests/static/state_tests/stStaticCall/static_callCreateFiller.json

callee code:
    push1 0x01
    push1 0x01
    push1 0x00
    create
    stop

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41
    push3 0x0249f0
    delegatecall
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0493e0
    staticcall
    push1 0x00
    sstore
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41
    push3 0x0249f0
    call
    stop

callee_3 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41
    push3 0x0249f0
    staticcall
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
    ["tests/static/state_tests/stStaticCall/static_callCreateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000f5c27325e6c5769b6569971cd81e01570fd30ef1",
        "00000000000000000000000029d4d72a31d1b141b2067d1d4193bdf12fcddc41",
        "000000000000000000000000b4aa7cc91d100eddc01f22ca32f643bb0f1c91cc",
        "000000000000000000000000f9ecfe0635fefb5ad44418f97d7fcaf210ebd5aa",
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_create(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xe49f04b30026f23e9e04493c44ece7cfec9224ca")
    callee = Address("0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41")
    callee_1 = Address("0xb4aa7cc91d100eddc01f22ca32f643bb0f1c91cc")
    callee_2 = Address("0xf5c27325e6c5769b6569971cd81e01570fd30ef1")
    callee_3 = Address("0xf9ecfe0635fefb5ad44418f97d7fcaf210ebd5aa")

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
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.CREATE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41] + Op.PUSH3[0x249f0]
        + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x493e0] + Op.STATICCALL
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41] + Op.PUSH3[0x249f0]
        + Op.STATICCALL + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=1000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
