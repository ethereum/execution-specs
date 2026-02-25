"""
Ported from:
tests/static/state_tests/stMemoryStressTest/mload32bitBound2Filler.json

contract code:
    push5 0x0177359400
    mload
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
    ["tests/static/state_tests/stMemoryStressTest/mload32bitBound2Filler.json"],
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
def test_mload32bit_bound2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x0f232941639f479d380d2712b0eec5d904482225")
    contract = Address("0xc287e277d2163771e55d630bdd96c6405a6fe251")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=37791080412587,
    )

    pre[sender] = Account(balance=0x157b5373e07ca, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH5[0x177359400] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
    )

    tx = Transaction(
        secret_key=Hash(
            "0xd566533f0ccab46749ac8725e15da8ce513758257002a8b481f6f5f96484c5ed"
        ),
        to=contract,
        data=b"",
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
