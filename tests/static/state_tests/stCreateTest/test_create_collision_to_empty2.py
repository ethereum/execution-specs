"""
data0 - create collision to empty, data1 - to empty but nonce, data2 - to contract with code

Ported from:
tests/static/state_tests/stCreateTest/CreateCollisionToEmpty2Filler.json

callee_1 code:
    push5 0x6001600155
    push1 0x00
    mstore
    push1 0x05
    push1 0x1b
    push1 0x00
    create
    push1 0x01
    sstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x013880
    call
    stop

callee_3 code:
    push5 0x6001600155
    push1 0x00
    mstore
    push1 0x05
    push1 0x1b
    push1 0x00
    create
    push1 0x01
    sstore
    stop

callee_4 code:
    push5 0x6001600155
    push1 0x00
    mstore
    push1 0x05
    push1 0x1b
    push1 0x00
    create
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
    ["tests/static/state_tests/stCreateTest/CreateCollisionToEmpty2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value",
    [
        ("0000000000000000000000001000000000000000000000000000000000000000", 600000, 0),
        ("0000000000000000000000001000000000000000000000000000000000000000", 600000, 1),
        ("0000000000000000000000001000000000000000000000000000000000000000", 54000, 0),
        ("0000000000000000000000001000000000000000000000000000000000000000", 54000, 1),
        ("0000000000000000000000002000000000000000000000000000000000000000", 600000, 0),
        ("0000000000000000000000002000000000000000000000000000000000000000", 600000, 1),
        ("0000000000000000000000002000000000000000000000000000000000000000", 54000, 0),
        ("0000000000000000000000002000000000000000000000000000000000000000", 54000, 1),
        ("0000000000000000000000003000000000000000000000000000000000000000", 600000, 0),
        ("0000000000000000000000003000000000000000000000000000000000000000", 600000, 1),
        ("0000000000000000000000003000000000000000000000000000000000000000", 54000, 0),
        ("0000000000000000000000003000000000000000000000000000000000000000", 54000, 1),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11'],
)
@pytest.mark.pre_alloc_mutable
def test_create_collision_to_empty2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
) -> None:
    """data0 - create collision to empty, data1 - to empty but nonce, data2 - to contract with code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x1a00000000000000000000000000000000000000")
    callee = Address("0x0bf4c804e0579073baf54ec4ec37cd04f3455c65")
    callee_1 = Address("0x1000000000000000000000000000000000000000")
    callee_2 = Address("0x13136008b64ff592819b2fa6d43f2835c452020e")
    callee_3 = Address("0x2000000000000000000000000000000000000000")
    callee_4 = Address("0x3000000000000000000000000000000000000000")
    callee_5 = Address("0x4b86c4ed99b87f0f396bc0c76885453c343916ed")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(balance=0, nonce=2)
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH5[0x6001600155] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x5]
        + Op.PUSH1[0x1b] + Op.PUSH1[0x0] + Op.CREATE + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_2] = Account(balance=10, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x13880]
        + Op.CALL + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH5[0x6001600155] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x5]
        + Op.PUSH1[0x1b] + Op.PUSH1[0x0] + Op.CREATE + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH5[0x6001600155] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x5]
        + Op.PUSH1[0x1b] + Op.PUSH1[0x0] + Op.CREATE + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_5] = Account(balance=0, nonce=0, code=bytes.fromhex("1122334455"))
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
