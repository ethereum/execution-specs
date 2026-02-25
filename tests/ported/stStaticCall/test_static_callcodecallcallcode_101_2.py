"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcodecallcallcode_101_2Filler.json

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0493e0
    staticcall
    stop

callee_1 code:
    push1 0x01
    push1 0x01
    mstore
    stop

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x01
    push20 0x2a142c79a9b097c111ce945214226126b75e332c
    push3 0x03d090
    callcode
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
    callvalue
    push20 0x1b78afbe56d4678cfa8dc79df079bad5585b8d3a
    push3 0x055730
    callcode
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_3 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x2a142c79a9b097c111ce945214226126b75e332c
    push3 0x03d090
    callcode
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
    ["tests/static/state_tests/stStaticCall/static_callcodecallcallcode_101_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000709eb538153d5f98f0b8482c462070c26db1cbae",
        "0000000000000000000000003cea889fd03a922cc673d25e5db4e72743aa4878",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcallcode_101_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x3f13b55c156d810bc161e971891180011e088e6f")
    callee = Address("0x1b78afbe56d4678cfa8dc79df079bad5585b8d3a")
    callee_1 = Address("0x2a142c79a9b097c111ce945214226126b75e332c")
    callee_2 = Address("0x3cea889fd03a922cc673d25e5db4e72743aa4878")
    callee_3 = Address("0x709eb538153d5f98f0b8482c462070c26db1cbae")

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
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x493e0] + Op.STATICCALL
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0x2a142c79a9b097c111ce945214226126b75e332c]
        + Op.PUSH3[0x3d090] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH20[0x1b78afbe56d4678cfa8dc79df079bad5585b8d3a] + Op.PUSH3[0x55730]
        + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x2a142c79a9b097c111ce945214226126b75e332c]
        + Op.PUSH3[0x3d090] + Op.CALLCODE + Op.STOP
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
