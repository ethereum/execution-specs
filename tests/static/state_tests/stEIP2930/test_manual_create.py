"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP2930/manualCreateFiller.yml
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP2930/manualCreateFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_access_list",
    [
        [AccessList(address=Address("0xec0e71ad0a90ffe1909d27dac207f7680abba42d"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000001")])],
        [AccessList(address=Address("0x0000000000000000000000000000000000000100"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])],
        [AccessList(address=Address("0xec0e71ad0a90ffe1909d27dac207f7680abba42d"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000")])],
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_manual_create(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_access_list,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0x1000000000000000000, nonce=1)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=None,
        data=bytes.fromhex("5a3031505a90036001555a60ff6000555a900360005500"),
        gas_limit=400000,
        gas_price=10,
        nonce=1,
        value=0,
        access_list=tx_access_list,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
