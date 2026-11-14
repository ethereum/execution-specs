"""
Example of PoS merge state test.

Ported from:
state_tests/stExample/mergeTestFiller.yml
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
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
def test_merge_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Example of PoS merge state test."""
    sender = pre.fund_eoa()

    # Source: lll
    # {
    #    (sstore 0 (gasprice))
    #    (sstore 1 (basefee))
    #    (sstore 2 (difficulty))
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.GASPRICE)
        + Op.SSTORE(key=0x1, value=Op.BASEFEE)
        + Op.SSTORE(key=0x2, value=Op.PREVRANDAO)
        + Op.STOP,
        nonce=1,
    )

    prev_randao = 0x15 << 248
    env = Environment(prev_randao=prev_randao, base_fee_per_gas=1000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=4000000,
        max_fee_per_gas=2000,
        max_priority_fee_per_gas=10,
        access_list=[
            AccessList(
                address=target,
                storage_keys=[Hash(0), Hash(1)],
            ),
        ],
    )

    post = {
        target: Account(
            storage={0: 1010, 1: 1000, 2: prev_randao},
            nonce=1,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
