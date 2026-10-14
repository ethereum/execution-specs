"""
Test_mload32bit_bound_msize.

Ported from:
state_tests/stMemoryStressTest/mload32bitBound_MsizeFiller.json
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
    ["state_tests/stMemoryStressTest/mload32bitBound_MsizeFiller.json"],
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
def test_mload32bit_bound_msize(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_mload32bit_bound_msize."""
    sender = pre.fund_eoa(amount=0x186A0C3B1E19A180)

    # Source: lll
    # { [4294967295] 1 [[ 0 ]] (MSIZE)}
    target_code = (
        Op.MSTORE(offset=0xFFFFFFFF, value=0x1)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP
    )
    target = pre.deploy_contract(
        code=target_code,
        balance=0xDE0B6B3A7640000,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={0: 0},
                    code=target_code,
                    nonce=1,
                ),
                sender: Account(storage={}, code=b"", nonce=1),
            },
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={0: 0},
                    code=target_code,
                    nonce=1,
                ),
                sender: Account(storage={}, code=b"", nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 16777216]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
