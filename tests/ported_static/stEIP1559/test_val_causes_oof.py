"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP1559/valCausesOOFFiller.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
]

TX_GAS = [100000, 90000, 110000]

TX_VALUE = [0, 1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP1559/valCausesOOFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(0, 0, 1, id="case1", marks=pytest.mark.exception_test),
        pytest.param(0, 1, 0, id="case2"),
        pytest.param(0, 1, 1, id="case3"),
        pytest.param(0, 2, 0, id="case4", marks=pytest.mark.exception_test),
        pytest.param(0, 2, 1, id="case5", marks=pytest.mark.exception_test),
        pytest.param(1, 0, 0, id="case6"),
        pytest.param(1, 0, 1, id="case7", marks=pytest.mark.exception_test),
        pytest.param(1, 1, 0, id="case8"),
        pytest.param(1, 1, 1, id="case9"),
        pytest.param(1, 2, 0, id="case10", marks=pytest.mark.exception_test),
        pytest.param(1, 2, 1, id="case11", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_val_causes_oof(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x7608AB0A661408930040C5E3EB5B0C6520ACBB6CE5B28DDBE53676109E8EA24B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0x5F5E100, nonce=1)
    # Source: Yul
    # {
    #     // This loop runs a number of times specified in the data,
    #     // so the gas cost depends on the data
    #     for { let i := calldataload(4) } gt(i,0) { i := sub(i,1) } {
    #        sstore(i, 0x60A7)
    #     }     // for loop
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x4)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xC, condition=Op.GT(Op.DUP2, 0x0))
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=Op.DUP2, value=0x60A7)
            + Op.NOT(0x0)
            + Op.ADD
            + Op.JUMP(pc=0x3)
        ),
        balance=0x5AF3107A4000,
        nonce=0,
        address=Address("0x71e12b76ab6be1efbc98ac17ebfe5faf488da45e"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0 - 1, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS"
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": -1, "gas": 2, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS"
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        max_fee_per_gas=1000,
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
