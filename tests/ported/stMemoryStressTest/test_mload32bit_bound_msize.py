"""
Ported from:
tests/static/state_tests/stMemoryStressTest/mload32bitBound_MsizeFiller.json

contract code:
    push1 0x01
    push4 0xffffffff
    mstore
    msize
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
    ["tests/static/state_tests/stMemoryStressTest/mload32bitBound_MsizeFiller.json"],
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
def test_mload32bit_bound_msize(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x3b6a01e6249f494f798b8ca3c0ecaf19a2187f54")
    contract = Address("0x15d5a32351458ff3dca214bd202c21f066031ae1")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=175923205248920000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH4[0xffffffff] + Op.MSTORE + Op.MSIZE + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x186a0c3b1e19a180, nonce=0)

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
