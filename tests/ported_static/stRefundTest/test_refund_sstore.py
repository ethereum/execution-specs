"""
Ori Pomerantz   qbzzt1@gmail.com

Ported from:
state_tests/stRefundTest/refundSSTOREFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    AccessList,
    Hash,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refundSSTOREFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x8c45b94dca330650c0392398fb2097bb64764e973720a845ee67605ffabf0c7c
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=1000,
        gas_limit=16777216,
    )

    # Source: yul
    # berlin 
    # {
    #    sstore(0,0x0)
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=Op.DUP1, value=0x0) + Op.STOP,
        storage={0: 24743},
        balance=0xde0b6b3a7640000,
        nonce=1,
        address=Address("0xf5f86b947fc07a75e19106a6b7e4953d431ad57f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xe8d631f190, nonce=1)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("00"),
        gas_limit=2601000,
        nonce=1,
        gas_price=1000,
        access_list=[
        ],
    )

    post = {sender: Account(balance=0xe8d4ee4e00)}

    state_test(env=env, pre=pre, post=post, tx=tx)
