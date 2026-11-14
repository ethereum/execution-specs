"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stExample/eip1559Filler.yml
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
    ["state_tests/stExample/eip1559Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_eip1559(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    sender = pre.fund_eoa()

    # Source: lll
    # {
    #    (sstore 0 (gasprice))
    #    (sstore 1 (basefee))
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.GASPRICE)
        + Op.SSTORE(key=0x1, value=Op.BASEFEE)
        + Op.STOP,
    )

    env = Environment(base_fee_per_gas=1000)

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

    post = {target: Account(storage={0: 1010, 1: 1000})}

    state_test(env=env, pre=pre, post=post, tx=tx)
