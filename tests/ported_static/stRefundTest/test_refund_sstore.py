"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stRefundTest/refundSSTOREFiller.yml
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
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
    fork: Fork,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    pre[sender] = Account(balance=0xE8D631F190, nonce=1)
    # Source: Yul
    # {
    #    sstore(0,0x0)
    # }
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=Op.DUP1, value=0x0) + Op.STOP,
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        address=Address("0xf5f86b947fc07a75e19106a6b7e4953d431ad57f"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("6000805500"))},
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=2601000,
        gas_price=1000,
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
