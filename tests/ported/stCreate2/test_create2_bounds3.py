"""
Ported from:
tests/static/state_tests/stCreate2/CREATE2_Bounds3Filler.json

contract code:
    push32 0x6001600155601080600c6000396000f3006000355415600957005b6020356000
    push1 0x00
    mstore
    push1 0x35
    push1 0x20
    mstore8
    push1 0x55
    push1 0x21
    mstore8
    push1 0x00
    push8 0xffffffffffffffff
    push1 0x00
    push1 0x01
    create2
    pop
    push1 0x00
    push16 0xffffffffffffffffffffffffffffffff
    push1 0x00
    push1 0x01
    create2
    ... (67 more instructions)
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
    ["tests/static/state_tests/stCreate2/CREATE2_Bounds3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        150000,
        1000000,
        16777216,
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_create2_bounds3(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x1000000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[contract] = Account(
        balance=100,
        nonce=0,
        code=(
        Op.PUSH32[0x6001600155601080600c6000396000f3006000355415600957005b6020356000]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x35] + Op.PUSH1[0x20] + Op.MSTORE8
        + Op.PUSH1[0x55] + Op.PUSH1[0x21] + Op.MSTORE8 + Op.PUSH1[0x0]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.CREATE2
        + Op.POP + Op.PUSH1[0x0] + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.CREATE2 + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.CREATE2 + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH4[0xfffffff] + Op.PUSH1[0x1] + Op.CREATE2 + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH4[0xffffffff] + Op.PUSH1[0x1]
        + Op.CREATE2 + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH1[0x1] + Op.CREATE2 + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x1] + Op.CREATE2
        + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x1] + Op.CREATE2 + Op.POP + Op.PUSH1[0x0] + Op.PUSH4[0xfffffff]
        + Op.PUSH4[0xfffffff] + Op.PUSH1[0x1] + Op.CREATE2 + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.PUSH1[0x1] + Op.CREATE2
        + Op.POP + Op.PUSH1[0x0] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH1[0x1] + Op.CREATE2 + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x1] + Op.CREATE2
        + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x1] + Op.CREATE2 + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xfffffffffffffffffffffffffffffffffffffffffffffffff, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
