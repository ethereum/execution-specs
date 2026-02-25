"""
Ori Pomerantz   qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stRefundTest/refundSSTOREFiller.yml

contract code:
    push1 0x00
    dup1
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
    ["tests/static/state_tests/stRefundTest/refundSSTOREFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xddc3963f450ae1a9db51c77d80166de70ce99cee")
    contract = Address("0xf5f86b947fc07a75e19106a6b7e4953d431ad57f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=16777216,
    )

    pre[sender] = Account(balance=0xe8d631f190, nonce=1)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=Op.PUSH1[0x0] + Op.DUP1 + Op.SSTORE + Op.STOP,
        storage={0x0: 0x60a7},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x8c45b94dca330650c0392398fb2097bb64764e973720a845ee67605ffabf0c7c"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=2601000,
        gas_price=1000,
        nonce=1,
        value=0,
        access_list=[],
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
