"""
Is a canon example of a test found by fuzzing with EVMlab, demoing how a...

Ported from:
tests/static/state_tests/stBugs
randomStatetestDEFAULT-Tue_07_58_41-15153-575192_londonFiller.json
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
    [
        "tests/static/state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192_londonFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest_default_minus_tue_07_58_41_minus_15153_minus_575192_london(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Is a canon example of a test found by fuzzing with EVMlab,..."""
    coinbase = Address("0xdf5277352f687058bec2d433f2e2d1b7f0c970ae")
    sender = EOA(
        key=0xEDDB5B1A0109F06919449A6279E9DE92A892086BDD851894EB8FFA6C8FF4E563
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=20000000,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0xABCDEF),
        nonce=28,
        address=Address("0x589d1b72331c25effee38732d79f48f729681853"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5D8FDD3FF54298B4, nonce=28)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PUSH2[0xDEAD]
            + Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.SSTORE(key=0x1, value=Op.EXTCODEHASH(address=0xABCDEF))
        ),
        nonce=28,
        address=coinbase,  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=coinbase,
        gas_limit=6282759,
        nonce=28,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
