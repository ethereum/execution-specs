"""
Ported from:
tests/static/state_tests/stBugs/staticcall_createfailsFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x011170
    staticcall
    push1 0x01
    sstore
    stop

callee code:
    push1 0x01
    push1 0x01
    mstore
    push1 0x01
    push1 0x01
    push1 0x01
    create
    push1 0x02
    sstore
    stop

callee_1 code:
    push1 0x00
    push1 0x00
    create
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
    ["tests/static/state_tests/stBugs/staticcall_createfailsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000c94f5374fce5edbc8e2a8697c15331677e6ebf0b",
        "000000000000000000000000d94f5374fce5edbc8e2a8697c15331677e6ebf0b",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_staticcall_createfails(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x1000000000000000000000000000000000000000")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee_1 = Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=23826461031063688,
    )

    pre[sender] = Account(balance=0x38beec8feeca2598, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=63,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x11170] + Op.STATICCALL
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
        storage={0x1: 0x1},
    )
    pre[callee] = Account(
        balance=0,
        nonce=63,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.CREATE + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(balance=0, nonce=63, code=Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=120000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
