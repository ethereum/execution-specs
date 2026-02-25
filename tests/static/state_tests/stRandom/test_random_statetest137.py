"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest137Filler.json

contract code:
    push32 0xffffffffffffffffffffffffffffffffffffffff
    push32 0x00
    push32 0x00
    addmod
    push32 0x010000000000000000000000000000000000000000
    push32 0x01
    push31 0x7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a
    push18 0xb5a130e86ca17390989355f092a255600051
    sstore

coinbase code:
    push1 0x00
    calldataload
    sload
    iszero
    push1 0x09
    jumpi
    stop
    jumpdest
    push1 0x20
    calldataload
    push1 0x00
    calldataload
    sstore
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
    ["tests/static/state_tests/stRandom/randomStatetest137Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest137(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff] + Op.PUSH32[0x0]
        + Op.PUSH32[0x0] + Op.ADDMOD
        + Op.PUSH32[0x10000000000000000000000000000000000000000] + Op.PUSH32[0x1]
        + Op.PUSH31[0x7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a]
        + Op.PUSH18[0xb5a130e86ca17390989355f092a255600051] + Op.SSTORE
    ),
    )
    pre[coinbase] = Account(
        balance=46,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SLOAD + Op.ISZERO + Op.PUSH1[0x9]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x20] + Op.CALLDATALOAD
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SSTORE
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex(
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000"
            "0000000000000000000000000000000000000000000000000000000000007f0000000000"
            "000000000000000000000000000000000000000000000000000000087f00000000000000"
            "000000000100000000000000000000000000000000000000007f00000000000000000000"
            "000000000000000000000000000000000000000000017e7f000000000000000000000000"
            "945304eb96065b2a98b57a48a06ae28d285a71b5a130e86ca17390989355f092a2"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=866944487,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
