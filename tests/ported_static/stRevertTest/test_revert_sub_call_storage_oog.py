"""
Test_revert_sub_call_storage_oog.

Ported from:
state_tests/stRevertTest/RevertSubCallStorageOOGFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertSubCallStorageOOGFiller.json"],
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
@pytest.mark.pre_alloc_mutable
def test_revert_sub_call_storage_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_sub_call_storage_oog."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: raw
    # 0x60606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff168063b28175c4146046578063c0406226146052575b6000565b3460005760506076565b005b34600057605c6081565b604051808215151515815260200191505060405180910390f35b600c6000819055505b565b600060896076565b600d600181905550600e600281905550600190505b905600a165627a7a723058202a8a75d7d795b5bcb9042fb18b283daa90b999a11ddec892f548732235342eb60029  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex(
            "60606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff168063b28175c4146046578063c0406226146052575b6000565b3460005760506076565b005b34600057605c6081565b604051808215151515815260200191505060405180910390f35b600c6000819055505b565b600060896076565b600d600181905550600e600281905550600190505b905600a165627a7a723058202a8a75d7d795b5bcb9042fb18b283daa90b999a11ddec892f548732235342eb60029"  # noqa: E501
        ),
        balance=1,
        nonce=0,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {target: Account(storage={}, balance=1, nonce=0)},
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={0: 12, 1: 13, 2: 14}, balance=1, nonce=0
                )
            },
        },
        {
            "indexes": {"data": -1, "gas": [0, 1], "value": 1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={}, balance=1, nonce=0)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("c0406226"),
    ]
    tx_gas = [81000, 181000]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
