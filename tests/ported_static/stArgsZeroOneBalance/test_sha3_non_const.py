"""
Test_sha3_non_const.

Ported from:
state_tests/stArgsZeroOneBalance/sha3NonConstFiller.yml
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
    ["state_tests/stArgsZeroOneBalance/sha3NonConstFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-v1",
        ),
    ],
)
def test_sha3_non_const(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_sha3_non_const."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { [[ 0 ]](KECCAK256 (BALANCE <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>) (BALANCE <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>)) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.SHA3(
                offset=Op.BALANCE(address=Op.ADDRESS),
                size=Op.BALANCE(address=Op.ADDRESS),
            ),
        )
        + Op.STOP,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": -1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A,  # noqa: E501
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [400000]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
