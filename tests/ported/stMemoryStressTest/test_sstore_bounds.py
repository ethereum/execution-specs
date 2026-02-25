"""
Ported from:
tests/static/state_tests/stMemoryStressTest/SSTORE_BoundsFiller.json

contract code:
    push1 0x01
    push4 0xffffffff
    sstore
    push1 0x01
    push8 0xffffffffffffffff
    sstore
    push1 0x01
    push16 0xffffffffffffffffffffffffffffffff
    sstore
    push1 0x01
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    sstore
    push4 0xffffffff
    push1 0x20
    sstore
    push8 0xffffffffffffffff
    push1 0x40
    sstore
    push16 0xffffffffffffffffffffffffffffffff
    push1 0x80
    ... (5 more instructions)
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
    ["tests/static/state_tests/stMemoryStressTest/SSTORE_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        150000,
        16777216,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xd468b4c11201f7d9c35fe33e663dba4f904e4748")
    contract = Address("0x1f2aee312c3c47bdeb27ff5275fddb33c543e394")

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
        Op.PUSH1[0x1] + Op.PUSH4[0xffffffff] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH8[0xffffffffffffffff] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.SSTORE + Op.PUSH4[0xffffffff] + Op.PUSH1[0x20] + Op.SSTORE
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH1[0x40] + Op.SSTORE
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x80] + Op.SSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH2[0x100] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x7ffffffffffffffffff, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xfe5be118ad5955e30e0ffc4e1f1bbdcaa7f5a67cb1426c4ac19e32c80eccdc06"
        ),
        to=contract,
        data=b"",
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
