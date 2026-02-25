"""
Ported from:
tests/static/state_tests/stMemoryStressTest/SLOAD_BoundsFiller.json

contract code:
    push1 0x00
    sload
    pop
    push4 0xffffffff
    sload
    pop
    push8 0xffffffffffffffff
    sload
    pop
    push16 0xffffffffffffffffffffffffffffffff
    sload
    pop
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    sload
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
    ["tests/static/state_tests/stMemoryStressTest/SLOAD_BoundsFiller.json"],
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
def test_sload_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xd468b4c11201f7d9c35fe33e663dba4f904e4748")
    contract = Address("0x1b71c198ea09541afb8301905a0a80d026ebfa17")

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
        Op.PUSH1[0x0] + Op.SLOAD + Op.POP + Op.PUSH4[0xffffffff] + Op.SLOAD + Op.POP
        + Op.PUSH8[0xffffffffffffffff] + Op.SLOAD + Op.POP
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.SLOAD + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.SLOAD + Op.STOP
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
