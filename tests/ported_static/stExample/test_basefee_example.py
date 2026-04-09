"""
A test shows basefee transaction example.

Ported from:
state_tests/stExample/basefeeExampleFiller.yml
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stExample/basefeeExampleFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_basefee_example(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A test shows basefee transaction example."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=70000000,
        gas_limit=68719476736,
    )

    # Source: lll
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (ADD 1 1)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=4000000,
        value=0x186A0,
        max_fee_per_gas=5000000000,
        max_priority_fee_per_gas=2,
        access_list=[
            AccessList(
                address=target,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),
                ],
            ),
        ],
    )

    post = {target: Account(storage={0: 2})}

    state_test(env=env, pre=pre, post=post, tx=tx)
