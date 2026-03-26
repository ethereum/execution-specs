"""
This is a canon example of a test found by fuzzing with EVMlab, demoing how a suicide-created-but-empty account has a non-zero codehash in geth

Ported from:
state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192_londonFiller.json
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
    ["state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192_londonFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest_default_minus_tue_07_58_41_minus_15153_minus_575192_london(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """This is a canon example of a test found by fuzzing with EVMlab, dem..."""
    coinbase = Address("0xdf5277352f687058bec2d433f2e2d1b7f0c970ae")
    sender = EOA(
        key=0xeddb5b1a0109f06919449a6279e9de92a892086bdd851894eb8ffa6c8ff4e563
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=20000000,
    )

    # Source: raw
    # 0x62abcdefff
    addr_0x000000000000000000000000000000000000dead = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0xabcdef),
        nonce=28,
        address=Address("0x589d1b72331c25effee38732d79f48f729681853"),  # noqa: E501
    )
    # Source: raw
    # 0x61dead6000600060006000600061dead5af162abcdef3f600155
    coinbase = pre.deploy_contract(
        code=Op.PUSH2[0xdead]
        + Op.CALL(gas=Op.GAS, address=0xdead, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.SSTORE(key=0x1, value=Op.EXTCODEHASH(address=0xabcdef)),
        nonce=28,
        address=Address("0xdf5277352f687058bec2d433f2e2d1b7f0c970ae"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5d8fdd3ff54298b4, nonce=28)


    tx = Transaction(
        sender=sender,
        to=coinbase,
        data=b'',
        gas_limit=6282759,
        nonce=28,
        gas_price=10,
    )

    post = {
        coinbase: Account(
                storage={},
                code=bytes.fromhex("61dead6000600060006000600061dead5af162abcdef3f600155"),  # noqa: E501
                nonce=28,
            ),
        sender: Account(storage={}, code=b"", nonce=29),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
