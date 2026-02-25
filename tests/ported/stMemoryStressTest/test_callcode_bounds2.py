"""
Ported from:
tests/static/state_tests/stMemoryStressTest/CALLCODE_Bounds2Filler.json

contract code:
    push4 0x0fffffff
    push4 0x0fffffff
    push4 0x0fffffff
    push4 0x0fffffff
    push1 0x00
    push20 0x849f53126ade5f72469029537296f2b6644d4d41
    push8 0x07ffffffffffffff
    callcode
    stop

callee code:
    push1 0x00
    sload
    push1 0x01
    add
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
    ["tests/static/state_tests/stMemoryStressTest/CALLCODE_Bounds2Filler.json"],
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
def test_callcode_bounds2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa99635038e8d9ab237a31179dd5c9087713f723a")
    contract = Address("0x814cc86eb9caa0e43cfea934fbb77c7917f5cc0e")
    callee = Address("0x849f53126ade5f72469029537296f2b6644d4d41")

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
        Op.PUSH4[0xfffffff] + Op.PUSH4[0xfffffff] + Op.PUSH4[0xfffffff]
        + Op.PUSH4[0xfffffff] + Op.PUSH1[0x0]
        + Op.PUSH20[0x849f53126ade5f72469029537296f2b6644d4d41]
        + Op.PUSH8[0x7ffffffffffffff] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(
        balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
        nonce=0,
    )

    tx = Transaction(
        secret_key=Hash(
            "0x50eadfb1030587ab3a993a6ecc073041fc3b45e119daa31a13d78c7e209631a5"
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
