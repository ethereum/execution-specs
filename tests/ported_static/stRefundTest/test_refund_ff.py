"""
Ori Pomerantz   qbzzt1@gmail.com

Ported from:
state_tests/stRefundTest/refundFFFiller.yml
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
    ["state_tests/stRefundTest/refundFFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_ff(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0xdddddddddddddddddddddddddddddddddddddddd = Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3")  # noqa: E501
    sender = EOA(
        key=0xd6b0676afde099a078f9d00f24d2c1cb4278546e1734927015023db0980a92c5
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
    #    selfdestruct(<eoa:0xdddddddddddddddddddddddddddddddddddddddd>)
    # }
    target = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3),
        nonce=1,
        address=Address("0xa45b53c7b70adf8ea2e910d0e826df8d895b2b49"),  # noqa: E501
    )
    pre[addr_0xdddddddddddddddddddddddddddddddddddddddd] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xe8d6599218, nonce=1)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("00"),
        gas_limit=2601000,
        nonce=1,
        gas_price=1000,
    )

    post = {sender: Account(balance=0xe8d4a51000)}

    state_test(env=env, pre=pre, post=post, tx=tx)
