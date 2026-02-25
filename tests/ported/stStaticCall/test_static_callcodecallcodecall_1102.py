"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcodecallcodecall_1102Filler.json

callee code:
    push1 0x01
    push1 0x01
    mstore
    stop

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    callvalue
    push20 0x91645bc90f22c32a683bb049dce8bcc61c541d82
    push3 0x055730
    callcode
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_1 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x01
    callvalue
    sub
    push20 0xef859513ae36c397c43170a2980741575916167b
    push3 0x0493e0
    callcode
    stop

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x2a142c79a9b097c111ce945214226126b75e332c
    push3 0x03d090
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
    ["tests/static/state_tests/stStaticCall/static_callcodecallcodecall_1102Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value",
    [
        0,
        1,
        2,
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcodecall_1102(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x4be1b24080b17ed1f5f4c0ff9cd820d764a32620")
    callee = Address("0x2a142c79a9b097c111ce945214226126b75e332c")
    callee_1 = Address("0x91645bc90f22c32a683bb049dce8bcc61c541d82")
    callee_2 = Address("0xef859513ae36c397c43170a2980741575916167b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.CALLVALUE + Op.PUSH20[0x91645bc90f22c32a683bb049dce8bcc61c541d82]
        + Op.PUSH3[0x55730] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.CALLVALUE + Op.SUB
        + Op.PUSH20[0xef859513ae36c397c43170a2980741575916167b] + Op.PUSH3[0x493e0]
        + Op.CALLCODE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x2a142c79a9b097c111ce945214226126b75e332c] + Op.PUSH3[0x3d090]
        + Op.STATICCALL + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
