"""
Test_sstore_bounds.

Ported from:
state_tests/stMemoryStressTest/SSTORE_BoundsFiller.json
"""

import pytest
from execution_testing import (
    EOA,
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stMemoryStressTest/SSTORE_BoundsFiller.json"],
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
def test_sstore_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_sstore_bounds."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xFE5BE118AD5955E30E0FFC4E1F1BBDCAA7F5A67CB1426C4AC19E32C80ECCDC06
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    # Source: lll
    # { (SSTORE 0xffffffff 1) (SSTORE 0xffffffffffffffff 1) (SSTORE 0xffffffffffffffffffffffffffffffff 1) (SSTORE 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 1) (SSTORE 32 0xffffffff) (SSTORE 64 0xffffffffffffffff) (SSTORE 128 0xffffffffffffffffffffffffffffffff) (SSTORE 256 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0xFFFFFFFF, value=0x1)
        + Op.SSTORE(key=0xFFFFFFFFFFFFFFFF, value=0x1)
        + Op.SSTORE(key=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, value=0x1)
        + Op.SSTORE(
            key=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            value=0x1,
        )
        + Op.SSTORE(key=0x20, value=0xFFFFFFFF)
        + Op.SSTORE(key=0x40, value=0xFFFFFFFFFFFFFFFF)
        + Op.SSTORE(key=0x80, value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.SSTORE(
            key=0x100,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x1F2AEE312C3C47BDEB27FF5275FDDB33C543E394),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFFFFF)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        32: 0xFFFFFFFF,
                        64: 0xFFFFFFFFFFFFFFFF,
                        128: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                        256: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                        0xFFFFFFFF: 1,
                        0xFFFFFFFFFFFFFFFF: 1,
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF: 1,
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF: 1,  # noqa: E501
                    },
                    balance=1,
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={}, balance=0)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
