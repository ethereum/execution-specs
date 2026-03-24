"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stRefundTest/refundFFFiller.yml
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRefundTest/refundFFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_ff(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xD6B0676AFDE099A078F9D00F24D2C1CB4278546E1734927015023DB0980A92C5
    )
    callee = Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=16777216,
    )

    pre[sender] = Account(balance=0xE8D6599218, nonce=1)
    pre[callee] = Account(balance=0, nonce=1)
    # Source: Yul
    # {
    #    selfdestruct(<eoa:0xdddddddddddddddddddddddddddddddddddddddd>)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0x7704D8A022A1BA8F3539FC82C7D7FB065ABC0DF3)
        ),
        address=Address("0xa45b53c7b70adf8ea2e910d0e826df8d895b2b49"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=2601000,
        gas_price=1000,
        nonce=1,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
