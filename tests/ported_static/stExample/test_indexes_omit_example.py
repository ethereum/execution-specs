"""
Expect section set -indexes field by default equal to -1.

Ported from:
state_tests/stExample/indexesOmitExampleFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stExample/indexesOmitExampleFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_indexes_omit_example(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Expect section set -indexes field by default equal to -1."""
    sender = pre.fund_eoa()

    # Source: lll
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (ADD 1 1)
    # }
    target_code = Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)) + Op.STOP
    target = pre.deploy_contract(
        code=target_code,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=400000,
        value=0x186A0,
    )

    post = {
        target: Account(
            storage={0: 2},
            code=target_code,
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
