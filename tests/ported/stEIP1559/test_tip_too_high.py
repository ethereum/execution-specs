"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP1559/tipTooHighFiller.yml

contract code:
    push1 0x02
    push1 0x00
    sstore
    stop
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP1559/tipTooHighFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_tip_too_high(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x8dab845a8398167a1c204f0e79540d619be8b473")
    contract = Address("0xec75f5d282f63da54cb0dad4ff8eaaa070d2da2b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )

    tx = Transaction(
        secret_key=Hash(
            "0xde0c95357363da5c1c5a73bd7c2781ca5c9fecc1014103b5e1d1e990ae8208ec"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=400000,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=1001,
        nonce=1,
        value=100000,
        access_list=[],
        error=TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
