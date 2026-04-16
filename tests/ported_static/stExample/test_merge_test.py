"""
Example of PoS merge state test.

Ported from:
state_tests/stExample/mergeTestFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stExample/mergeTestFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_merge_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Example of PoS merge state test."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xDE0C95357363DA5C1C5A73BD7C2781CA5C9FECC1014103B5E1D1E990AE8208EC
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x1500000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
        base_fee_per_gas=1000,
        gas_limit=16777216,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    # Source: lll
    # {
    #    (sstore 0 (gasprice))
    #    (sstore 1 (basefee))
    #    (sstore 2 (difficulty))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.GASPRICE)
        + Op.SSTORE(key=0x1, value=Op.BASEFEE)
        + Op.SSTORE(key=0x2, value=Op.PREVRANDAO)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x49A0FE79E28D1D65E16CDF53ACAFEAE7BACCAC0E),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=4000000,
        max_fee_per_gas=2000,
        max_priority_fee_per_gas=10,
        nonce=1,
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

    post = {
        target: Account(
            storage={
                0: 1010,
                1: 1000,
                2: 0x1500000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
            },
            nonce=1,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
