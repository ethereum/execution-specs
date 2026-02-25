"""
Ported from:
tests/static/state_tests/stArgsZeroOneBalance/addmodNonConstFiller.yml

contract code:
    push20 0x92d2fc80312acd8c37857696d2224af18ce6f966
    balance
    push20 0x92d2fc80312acd8c37857696d2224af18ce6f966
    balance
    push20 0x92d2fc80312acd8c37857696d2224af18ce6f966
    balance
    addmod
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
    ["tests/static/state_tests/stArgsZeroOneBalance/addmodNonConstFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value",
    [
        0,
        1,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_addmod_non_const(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x92d2fc80312acd8c37857696d2224af18ce6f966")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH20[0x92d2fc80312acd8c37857696d2224af18ce6f966] + Op.BALANCE
        + Op.PUSH20[0x92d2fc80312acd8c37857696d2224af18ce6f966] + Op.BALANCE
        + Op.PUSH20[0x92d2fc80312acd8c37857696d2224af18ce6f966] + Op.BALANCE
        + Op.ADDMOD + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=b"",
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
