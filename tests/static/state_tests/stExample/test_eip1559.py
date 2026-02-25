"""
Ori Pomerantz   qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stExample/eip1559Filler.yml

contract code:
    gasprice
    push1 0x00
    sstore
    basefee
    push1 0x01
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stExample/eip1559Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_eip1559(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x8dab845a8398167a1c204f0e79540d619be8b473")
    contract = Address("0x38dc047054d46298a5bb7ed3a0bad84bf69090d4")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=16777216,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.GASPRICE + Op.PUSH1[0x0] + Op.SSTORE + Op.BASEFEE + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)

    tx = Transaction(
        secret_key=Hash(
            "0xde0c95357363da5c1c5a73bd7c2781ca5c9fecc1014103b5e1d1e990ae8208ec"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=4000000,
        max_fee_per_gas=2000,
        max_priority_fee_per_gas=10,
        nonce=1,
        value=0,
        access_list=[AccessList(address=Address("0x38dc047054d46298a5bb7ed3a0bad84bf69090d4"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x0000000000000000000000000000000000000000000000000000000000000001")])],
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
