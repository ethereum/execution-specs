"""
Example of PoS merge state test

Ported from:
state_tests/stExample/mergeTestFiller.yml
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
    ["state_tests/stExample/mergeTestFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_merge_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Example of PoS merge state test"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xde0c95357363da5c1c5a73bd7c2781ca5c9fecc1014103b5e1d1e990ae8208ec
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x1500000000000000000000000000000000000000000000000000000000000000,
        difficulty=0x20000,
        base_fee_per_gas=1000,
        gas_limit=16777216,
    )

    # Source: lll
    # {
    #    (sstore 0 (gasprice))
    #    (sstore 1 (basefee))
    #    (sstore 2 (difficulty))
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.GASPRICE)
        + Op.SSTORE(key=0x1, value=Op.BASEFEE)
        + Op.SSTORE(key=0x2, value=Op.PREVRANDAO) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=1,
        address=Address("0x49a0fe79e28d1d65e16cdf53acafeae7baccac0e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("00"),
        gas_limit=4000000,
        max_fee_per_gas=2000,
        max_priority_fee_per_gas=10,
        nonce=1,
        access_list=[
            AccessList(
                address=Address("0x49a0fe79e28d1d65e16cdf53acafeae7baccac0e"),
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
            2: 0x1500000000000000000000000000000000000000000000000000000000000000,
        },
                nonce=1,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
