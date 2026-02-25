"""
Ported from:
tests/static/state_tests/stMemoryStressTest/DUP_BoundsFiller.json

contract code:
    push1 0x00
    dup1
    pop
    pop
    push4 0xffffffff
    dup1
    pop
    pop
    push8 0xffffffffffffffff
    dup1
    pop
    pop
    push16 0xffffffffffffffffffffffffffffffff
    dup1
    pop
    pop
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    dup1
    pop
    pop
    ... (411 more instructions)
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
    ["tests/static/state_tests/stMemoryStressTest/DUP_BoundsFiller.json"],
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
def test_dup_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xf2f6c03017e58b15115443223a6a0f8a4363b5c1")
    contract = Address("0xe860bd7bf0474923e526cbe86fa5b5f76aee36ed")

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
        Op.PUSH1[0x0] + Op.DUP1 + Op.POP + Op.POP + Op.PUSH4[0xffffffff] + Op.DUP1
        + Op.POP + Op.POP + Op.PUSH8[0xffffffffffffffff] + Op.DUP1 + Op.POP + Op.POP
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.DUP1 + Op.POP + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.DUP1 + Op.POP + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP2 + Op.POP
        + Op.POP + Op.POP + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.DUP2
        + Op.POP + Op.POP + Op.POP + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.DUP2 + Op.POP + Op.POP + Op.POP
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.DUP2 + Op.POP + Op.POP
        + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.DUP2 + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.DUP3 + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.DUP3
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff] + Op.DUP3
        + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.DUP3 + Op.POP + Op.POP
        + Op.POP + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.DUP3 + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP4 + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff]
        + Op.PUSH4[0xffffffff] + Op.DUP4 + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff] + Op.DUP4
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.DUP4 + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.DUP4 + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP5
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH4[0xffffffff]
        + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff]
        + Op.PUSH4[0xffffffff] + Op.DUP5 + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.DUP5 + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.DUP5 + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.DUP5 + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP6 + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff]
        + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff]
        + Op.PUSH4[0xffffffff] + Op.DUP6 + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.DUP6 + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.DUP6 + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.DUP6 + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP7 + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH4[0xffffffff]
        + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff]
        + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.DUP7
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.DUP7 + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.DUP7 + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.DUP7 + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP8
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff]
        + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff]
        + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.DUP8 + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff] + Op.DUP8
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.DUP8 + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.DUP8
    ),
    )
    pre[sender] = Account(balance=0x7fffffffffffffff, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x31b5af02b012484ae954b3a43943242ede546a2e76fc0a6acc17435107c385eb"
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
