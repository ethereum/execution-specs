"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stRefundTest/refundSSTOREFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
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
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x8C45B94DCA330650C0392398FB2097BB64764E973720A845EE67605FFABF0C7C
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=16777216,
    )

    # Source: yul
    # berlin
    # {
    #    sstore(0,0x0)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=Op.DUP1, value=0x0) + Op.STOP,
        storage={0: 24743},
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0xF5F86B947FC07A75E19106A6B7E4953D431AD57F),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D631F190, nonce=1)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=2601000,
        nonce=1,
        gas_price=1000,
        access_list=[],
    )

    post = {sender: Account(balance=0xE8D4EE4E00)}

    state_test(env=env, pre=pre, post=post, tx=tx)
