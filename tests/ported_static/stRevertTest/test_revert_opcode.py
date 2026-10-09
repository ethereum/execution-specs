"""
Test_revert_opcode.

Ported from:
state_tests/stRevertTest/RevertOpcodeFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertOpcodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-g0-v1",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="-g1-v1",
        ),
    ],
)
def test_revert_opcode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_opcode."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: raw
    # 0x600160005560016000fd6011600155
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.SSTORE(key=0x1, value=0x11),
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(storage={}, balance=0),
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(storage={}, balance=0),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [800000, 30000]
    tx_value = [0, 10]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
