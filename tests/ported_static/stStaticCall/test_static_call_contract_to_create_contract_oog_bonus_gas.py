"""
Gas analysis showed this test's gas can go as low as 101174, and still...

Ported from:
state_tests/stStaticCall/static_CallContractToCreateContractOOGBonusGasFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_CallContractToCreateContractOOGBonusGasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
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
def test_static_call_contract_to_create_contract_oog_bonus_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Gas analysis showed this test's gas can go as low as 101174, and..."""
    sender = pre.fund_eoa(amount=0x2540BE400)

    # Source: lll
    # { (MSTORE 0 0x600c60005566602060406000f060205260076039f3) [[0]](CREATE 1 11 21) [[ 1 ]] (STATICCALL 0 (SLOAD 0) 0 0 0 0)}  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0, value=0x600C60005566602060406000F060205260076039F3
        )
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0xB, size=0x15))
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x0,
                address=Op.SLOAD(key=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=112,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_0: Account(
                    storage={
                        0: compute_create_address(address=contract_0, nonce=1),
                    },
                    nonce=2,
                ),
                sender: Account(nonce=1),
                compute_create_address(address=contract_0, nonce=1): Account(
                    storage={0: 12, 1: 0}, balance=1, nonce=1
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_0: Account(storage={0: 0}, nonce=1),
                sender: Account(nonce=1),
                compute_create_address(
                    address=contract_0, nonce=1
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [20000000, 80000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
