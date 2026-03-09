"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryStressTest/JUMPI_BoundsFiller.json
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
    ["tests/static/state_tests/stMemoryStressTest/JUMPI_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (150000, {}),
        (16777216, {}),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_jumpi_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x31B5AF02B012484AE954B3A43943242EDE546A2E76FC0A6ACC17435107C385EB
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: LLL
    # { (JUMPI 0xffffffff 1) (JUMPI 0xffffffffffffffff 1) (JUMPI 0xffffffffffffffffffffffffffffffff 1) (JUMPI 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 1) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0xFFFFFFFF, condition=0x1)
            + Op.JUMPI(pc=0xFFFFFFFFFFFFFFFF, condition=0x1)
            + Op.JUMPI(pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, condition=0x1)
            + Op.JUMPI(
                pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                condition=0x1,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x147f3300e29f2f09880e97b81f7b3ebcf78863e9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFF)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
