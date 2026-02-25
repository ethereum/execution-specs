"""
Ported from:
tests/static/state_tests/stSystemOperationsTest/ABAcallsSuicide0Filler.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x18
    push20 0x24940009f045e4134ed2ab242be610d312fe9a29
    push3 0x0186a0
    call
    pc
    sstore
    push20 0x24940009f045e4134ed2ab242be610d312fe9a29
    selfdestruct
    stop

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x17
    push20 0x10481e52c494fd0d78604b0f9207a89008f7e9a9
    push2 0xc350
    call
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
    ["tests/static/state_tests/stSystemOperationsTest/ABAcallsSuicide0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ab_acalls_suicide0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x10481e52c494fd0d78604b0f9207a89008f7e9a9")
    callee = Address("0x24940009f045e4134ed2ab242be610d312fe9a29")

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
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x18] + Op.PUSH20[0x24940009f045e4134ed2ab242be610d312fe9a29]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.PC + Op.SSTORE
        + Op.PUSH20[0x24940009f045e4134ed2ab242be610d312fe9a29] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x17] + Op.PUSH20[0x10481e52c494fd0d78604b0f9207a89008f7e9a9]
        + Op.PUSH2[0xc350] + Op.CALL + Op.PUSH1[0x1] + Op.ADD + Op.PC + Op.SSTORE
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
        gas_limit=10000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
