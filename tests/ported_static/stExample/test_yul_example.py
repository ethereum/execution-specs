"""
An example test for using simple yul contracts in the test.

Ported from:
state_tests/stExample/yulExampleFiller.yml
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
    ["state_tests/stExample/yulExampleFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_yul_example(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """An example test for using simple yul contracts in the test."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x40AC0FC28C27E961EE46EC43355A094DE205856EDBD4654CF2577C2608D4EC1E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

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
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x3) + Op.RETURN(offset=0x0, size=0x20),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xf30c160326a04ecb32e7651c0a8f373468bea269"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx = Transaction(
        sender=sender,
        to=target,
        data=b"",
        gas_limit=16777216,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 3})}

    state_test(env=env, pre=pre, post=post, tx=tx)
