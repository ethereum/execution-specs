"""
Ported from:
tests/static/state_tests/stStaticCall/static_log_CallerFiller.json

callee code:
    push1 0xff
    push1 0x00
    mstore8
    caller
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    log4
    stop

callee_1 code:
    push1 0xff
    push1 0x00
    mstore8
    caller
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    log3
    stop

callee_2 code:
    push1 0xff
    push1 0x00
    mstore8
    caller
    push1 0x20
    push1 0x00
    log1
    stop

callee_3 code:
    push1 0xff
    push1 0x00
    mstore8
    caller
    push1 0x00
    push1 0x20
    push1 0x00
    log2
    stop

callee_4 code:
    push1 0xff
    push1 0x00
    mstore8
    push1 0x20
    push1 0x00
    log0
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push2 0xc350
    staticcall
    push1 0x00
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
    ["tests/static/state_tests/stStaticCall/static_log_CallerFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000c725abae869e29a5448dca5b51a58f0c960d4069",
        "000000000000000000000000842936958d62030200fbcef4371460d8a9400d05",
        "000000000000000000000000861cccbd560d81a33aac05190e986540663c6bba",
        "0000000000000000000000006c5da6457f756a77c392c72fe884f7f650428aef",
        "000000000000000000000000586cfaa42db8b743452a87549943ac07a09de5cc",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4'],
)
@pytest.mark.pre_alloc_mutable
def test_static_log_caller(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xd8c1fcdb2990f08e5fe821bf5af85f34201ba79a")
    callee = Address("0x586cfaa42db8b743452a87549943ac07a09de5cc")
    callee_1 = Address("0x6c5da6457f756a77c392c72fe884f7f650428aef")
    callee_2 = Address("0x842936958d62030200fbcef4371460d8a9400d05")
    callee_3 = Address("0x861cccbd560d81a33aac05190e986540663c6bba")
    callee_4 = Address("0xc725abae869e29a5448dca5b51a58f0c960d4069")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH1[0x0] + Op.MSTORE8 + Op.CALLER + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.LOG4
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH1[0x0] + Op.MSTORE8 + Op.CALLER + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.LOG3 + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH1[0x0] + Op.MSTORE8 + Op.CALLER + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.LOG1 + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH1[0x0] + Op.MSTORE8 + Op.CALLER + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.LOG2 + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH1[0x0] + Op.MSTORE8 + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.LOG0 + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH2[0xc350] + Op.STATICCALL
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
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
        gas_limit=210000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
