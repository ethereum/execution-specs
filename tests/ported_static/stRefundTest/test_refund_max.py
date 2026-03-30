"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stRefundTest/refundMaxFiller.yml
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
    ["state_tests/stRefundTest/refundMaxFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_max(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xB5555C6F8171A6EB3C0A84ED8F01AF5CE65A85A096A824A60EE5E2C2C2E076D1
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
    #    let newVal := 0
    #    sstore(0x00,newVal)
    #    sstore(0x01,newVal)
    #    sstore(0x02,newVal)
    #    sstore(0x03,newVal)
    #    sstore(0x04,newVal)
    #    sstore(0x05,newVal)
    #    sstore(0x06,newVal)
    #    sstore(0x07,newVal)
    #
    #    // Get rid of Yul optimizations
    #    newVal := msize()
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.SSTORE(key=0x0, value=Op.DUP1)
        + Op.SSTORE(key=0x1, value=Op.DUP1)
        + Op.SSTORE(key=0x2, value=Op.DUP1)
        + Op.SSTORE(key=0x3, value=Op.DUP1)
        + Op.SSTORE(key=0x4, value=Op.DUP1)
        + Op.SSTORE(key=0x5, value=Op.DUP1)
        + Op.SSTORE(key=0x6, value=Op.DUP1)
        + Op.PUSH1[0x7]
        + Op.SSTORE
        + Op.STOP,
        storage={
            0: 24743,
            1: 24743,
            2: 24743,
            3: 24743,
            4: 24743,
            5: 24743,
            6: 24743,
            7: 24743,
        },
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x7E9D1FF50F8EB9591A0434ABFE3230054A934124),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D848C3A0, nonce=1)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=2601000,
        nonce=1,
        gas_price=1000,
        access_list=[],
    )

    post = {sender: Account(balance=0xE8D55F7E90)}

    state_test(env=env, pre=pre, post=post, tx=tx)
