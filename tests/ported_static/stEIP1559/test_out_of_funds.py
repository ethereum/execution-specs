"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP1559/outOfFundsFiller.yml
"""

import pytest
from execution_testing import (
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP1559/outOfFundsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="declaredKeyWrite-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            0,
            1,
            id="declaredKeyWrite-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            1,
            0,
            id="declaredKeyWrite-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="declaredKeyWrite-g1-v1",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_out_of_funds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    # Source: yul
    # berlin {
    #     sstore(0, add(1,1))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x2) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("00"),
    ]
    tx_gas = [16777216, 40000]
    tx_value = [0, 1000000000000000000]
    tx_access_lists: dict[int, list] = {
        0: [],
    }

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        max_fee_per_gas=100000000000,
        max_priority_fee_per_gas=100000000000,
        nonce=1,
        access_list=tx_access_lists.get(d),
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
