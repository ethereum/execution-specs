"""
Test: this is a canon example of a test found by fuzzing with EVMlab,...

Ported from:
state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192_londonFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192_londonFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest_default_minus_tue_07_58_41_minus_15153_minus_575192_london(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test: tis is a canon example of a test found by fuzzing with EVMlab,..."""  # noqa: E501
    coinbase = Address(0xDF5277352F687058BEC2D433F2E2D1B7F0C970AE)
    sender = pre.fund_eoa(amount=0x5D8FDD3FF54298B4, nonce=28)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=20000000,
    )

    # Source: raw
    # 0x62abcdefff
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0xABCDEF),
        nonce=28,
    )
    # Source: raw
    # 0x61dead6000600060006000600061dead5af162abcdef3f600155
    coinbase = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH2[0xDEAD]
        + Op.CALL(
            gas=Op.GAS,
            address=0xDEAD,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.SSTORE(key=0x1, value=Op.EXTCODEHASH(address=0xABCDEF)),
        nonce=28,
        address=Address(0xDF5277352F687058BEC2D433F2E2D1B7F0C970AE),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=coinbase,
        data=Bytes(""),
        gas_limit=6282759,
        nonce=28,
    )

    post = {
        coinbase: Account(
            storage={},
            code=bytes.fromhex(
                "61dead6000600060006000600061dead5af162abcdef3f600155"
            ),
            nonce=28,
        ),
        sender: Account(storage={}, code=b"", nonce=29),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
