"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryStressTest/POP_BoundsFiller.json
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
    "",
]

TX_GAS = [150000, 16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stMemoryStressTest/POP_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 1, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_pop_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xFE5BE118AD5955E30E0FFC4E1F1BBDCAA7F5A67CB1426C4AC19E32C80ECCDC06
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
    # { (POP 0) (POP 0xffffffff) (POP 0xffffffffffffffff) (POP 0xffffffffffffffffffffffffffffffff) (POP 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(0x0)
            + Op.POP(0xFFFFFFFF)
            + Op.POP(0xFFFFFFFFFFFFFFFF)
            + Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.POP(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x5bd3610afcec3b0c20466ca011b505497b0009f0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFFFFF)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "60005063ffffffff5067ffffffffffffffff506fffffffffffffffffffffffffffffffff507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5000"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "60005063ffffffff5067ffffffffffffffff506fffffffffffffffffffffffffffffffff507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5000"  # noqa: E501
                    )
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
