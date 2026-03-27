"""
Test_jumpi_bounds.

Ported from:
state_tests/stMemoryStressTest/JUMPI_BoundsFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "",
]
TX_GAS = [150000, 16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stMemoryStressTest/JUMPI_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_jumpi_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_jumpi_bounds."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x31B5AF02B012484AE954B3A43943242EDE546A2E76FC0A6ACC17435107C385EB
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: lll
    # { (JUMPI 0xffffffff 1) (JUMPI 0xffffffffffffffff 1) (JUMPI 0xffffffffffffffffffffffffffffffff 1) (JUMPI 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 1) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0xFFFFFFFF, condition=0x1)
        + Op.JUMPI(pc=0xFFFFFFFFFFFFFFFF, condition=0x1)
        + Op.JUMPI(pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, condition=0x1)
        + Op.JUMPI(
            pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            condition=0x1,
        )
        + Op.STOP,
        nonce=0,
        address=Address("0x147f3300e29f2f09880e97b81f7b3ebcf78863e9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFF)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    code=bytes.fromhex(
                        "600163ffffffff57600167ffffffffffffffff5760016fffffffffffffffffffffffffffffffff5760017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5700"  # noqa: E501
                    ),
                    balance=0,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
