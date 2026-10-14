"""
An example test for using simple yul contracts in the test.

Ported from:
state_tests/stExample/yulExampleFiller.yml
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
    ["state_tests/stExample/yulExampleFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_yul_example(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """An example test for using simple yul contracts in the test."""
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

    # Source: yul
    # berlin
    # {
    #   function f(a, b) -> c {
    #     c := add(a, b)
    #   }
    #
    #   sstore(0, f(1, 2))
    #   return(0, 32)
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x3) + Op.RETURN(offset=0x0, size=0x20),
        balance=0xBA1A9CE0BA1A9CE,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=16777216,
    )

    post = {target: Account(storage={0: 3})}

    state_test(pre=pre, post=post, tx=tx)
