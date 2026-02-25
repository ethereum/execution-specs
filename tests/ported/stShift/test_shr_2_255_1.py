"""
Taken from https://github.com/ethereum/EIPs/blob/master/EIPS/eip-145.md

Ported from:
tests/static/state_tests/stShift/shr_2^255_1Filler.json

contract code:
    push32 0x8000000000000000000000000000000000000000000000000000000000000000
    push1 0x01
    shr
    push1 0x00
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
    ["tests/static/state_tests/stShift/shr_2^255_1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_shr_2_255_1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Taken from https://github.com/ethereum/EIPs/blob/master/EIPS/eip-145.md."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xa389b98748a90663fa4e2b16d2ae848ebc2069d2")

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
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH32[0x8000000000000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x1] + Op.SHR + Op.PUSH1[0x0] + Op.SSTORE
    ),
        storage={0x0: 0x3},
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
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
