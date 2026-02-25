"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcodecallcallcode_ABCB_RECURSIVE2Filler.json

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x2733821fa13c4ead1c9631c76820333f42059b7c
    push3 0x07a120
    callcode
    stop

callee_1 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x1a3c543695d7ca3a7d5522e9c7aabe5512571706
    push3 0x0f4240
    staticcall
    stop

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xb81eb378451b4361df035aea57913023dffbf39a
    push3 0x0f4240
    staticcall
    stop

callee_3 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x01
    push20 0x6acc177800643d95ab1daee1bd55cf99e3814e07
    push3 0x07a120
    callcode
    stop

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    callvalue
    push1 0x00
    calldataload
    push4 0x017d7840
    callcode
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
    ["tests/static/state_tests/stStaticCall/static_callcodecallcallcode_ABCB_RECURSIVE2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_value",
    [
        ("0000000000000000000000002733821fa13c4ead1c9631c76820333f42059b7c", 0),
        ("0000000000000000000000002733821fa13c4ead1c9631c76820333f42059b7c", 1),
        ("0000000000000000000000006acc177800643d95ab1daee1bd55cf99e3814e07", 0),
        ("0000000000000000000000006acc177800643d95ab1daee1bd55cf99e3814e07", 1),
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcallcode_abcb_recursive2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xba3c5101ad0b43de0f1853243eb3f9811eaee1e0")
    callee = Address("0x1a3c543695d7ca3a7d5522e9c7aabe5512571706")
    callee_1 = Address("0x2733821fa13c4ead1c9631c76820333f42059b7c")
    callee_2 = Address("0x6acc177800643d95ab1daee1bd55cf99e3814e07")
    callee_3 = Address("0xb81eb378451b4361df035aea57913023dffbf39a")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    pre[callee] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x2733821fa13c4ead1c9631c76820333f42059b7c]
        + Op.PUSH3[0x7a120] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1a3c543695d7ca3a7d5522e9c7aabe5512571706] + Op.PUSH3[0xf4240]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb81eb378451b4361df035aea57913023dffbf39a] + Op.PUSH3[0xf4240]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0x6acc177800643d95ab1daee1bd55cf99e3814e07]
        + Op.PUSH3[0x7a120] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.CALLVALUE + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH4[0x17d7840]
        + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
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
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
