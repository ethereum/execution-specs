"""
Calling a runtime code that contains only a single `REVERT` should...

Ported from:
state_tests/stRevertTest/RevertOnEmptyStackFiller.json
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
    ["state_tests/stRevertTest/RevertOnEmptyStackFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_on_empty_stack(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Calling a runtime code that contains only a single `REVERT` should..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x3327048BBC0B8C348A6352BE62994144E64B8FF2CEC68D9FF4CA4E911ECD5D22
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x5AF3107A4000)
    # Source: raw
    # 0xfd
    target = pre.deploy_contract(  # noqa: F841
        code=Op.REVERT,
        nonce=0,
        address=Address("0x3141bb954e8294e47a14ebd08229f30e6294ba83"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=2000000,
        gas_price=10,
    )

    post = {sender: Account(balance=0x5AF30F491300, nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
