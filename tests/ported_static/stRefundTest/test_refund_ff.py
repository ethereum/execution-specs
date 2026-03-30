"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stRefundTest/refundFFFiller.yml
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
    ["state_tests/stRefundTest/refundFFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_ff(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr = Address(0x7704D8A022A1BA8F3539FC82C7D7FB065ABC0DF3)
    sender = EOA(
        key=0xD6B0676AFDE099A078F9D00F24D2C1CB4278546E1734927015023DB0980A92C5
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
    #    selfdestruct(<eoa:0xdddddddddddddddddddddddddddddddddddddddd>)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x7704D8A022A1BA8F3539FC82C7D7FB065ABC0DF3
        ),
        nonce=1,
        address=Address(0xA45B53C7B70ADF8EA2E910D0E826DF8D895B2B49),  # noqa: E501
    )
    pre[addr] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xE8D6599218, nonce=1)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=2601000,
        nonce=1,
        gas_price=1000,
        access_list=[],
    )

    post = {sender: Account(balance=0xE8D4A51000)}

    state_test(env=env, pre=pre, post=post, tx=tx)
