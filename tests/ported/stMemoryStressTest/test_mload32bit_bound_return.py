"""
Ported from:
tests/static/state_tests/stMemoryStressTest/mload32bitBound_returnFiller.json

contract code:
    push4 0xffffffff
    push1 0x00
    return
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
    ["tests/static/state_tests/stMemoryStressTest/mload32bitBound_returnFiller.json"],
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
def test_mload32bit_bound_return(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x3b6a01e6249f494f798b8ca3c0ecaf19a2187f54")
    contract = Address("0xd9cba08b7a9695800f57e226045176cf420ca0c1")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=17592320524892,
    )

    pre[sender] = Account(balance=0x186a0c3b1e19a180, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH4[0xffffffff] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP,
    )

    tx = Transaction(
        secret_key=Hash(
            "0x7dd14755c573e37c1f649b0c53b9815f76aebd636df7ccfa97f4579f33ba59a0"
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
