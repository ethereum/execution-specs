"""
Test_stack_overflow_m1_dup.

Ported from:
state_tests/stStackTests/stackOverflowM1DUPFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStackTests/stackOverflowM1DUPFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8",
        ),
        pytest.param(
            9,
            0,
            0,
            id="d9",
        ),
        pytest.param(
            10,
            0,
            0,
            id="d10",
        ),
        pytest.param(
            11,
            0,
            0,
            id="d11",
        ),
        pytest.param(
            12,
            0,
            0,
            id="d12",
        ),
        pytest.param(
            13,
            0,
            0,
            id="d13",
        ),
        pytest.param(
            14,
            0,
            0,
            id="d14",
        ),
        pytest.param(
            15,
            0,
            0,
            id="d15",
        ),
    ],
)
def test_stack_overflow_m1_dup(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_stack_overflow_m1_dup."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A5100000000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    contract_0 = pre.fund_eoa(amount=0xE8D4A5100000000000)  # noqa: F841

    tx_data = [
        Op.PUSH1[0x1] + Op.DUP1 * 1023,
        Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DUP2 * 1022,
        Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.PUSH1[0x3] + Op.DUP3 * 1021,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.DUP4 * 1020,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.DUP5 * 1019,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.DUP6 * 1018,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x7]
        + Op.DUP7 * 1017,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x8]
        + Op.DUP8 * 1016,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x9]
        + Op.DUP9 * 1015,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x10]
        + Op.DUP10 * 1014,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x11]
        + Op.DUP11 * 1013,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x12]
        + Op.DUP12 * 1012,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x13]
        + Op.DUP13 * 1011,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x13]
        + Op.PUSH1[0x14]
        + Op.DUP14 * 1010,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x13]
        + Op.PUSH1[0x14]
        + Op.PUSH1[0x15]
        + Op.DUP15 * 1009,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x13]
        + Op.PUSH1[0x14]
        + Op.PUSH1[0x15]
        + Op.PUSH1[0x16]
        + Op.DUP16 * 1008,
    ]
    tx_gas = [6000000]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(balance=1)
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
