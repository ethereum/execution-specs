"""
Test_out_of_gas_contract_creation.

Ported from:
state_tests/stInitCodeTest/OutOfGasContractCreationFiller.json
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stInitCodeTest/OutOfGasContractCreationFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_out_of_gas_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_out_of_gas_contract_creation."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000000,
    )

    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                compute_create_address(
                    address=sender, nonce=0
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                compute_create_address(
                    address=sender, nonce=0
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.PUSH1[0xA]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.CALLCODE
        + Op.STOP
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.BYTE(Op.DUP2, Op.CALLDATALOAD(offset=Op.DUP1))
        + Op.DUP2
        + Op.STOP,
        Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.SSTORE(key=0x1, value=0x3)
        + Op.SSTORE(key=0x1, value=0x4)
        + Op.SSTORE(key=0x1, value=0x5)
        + Op.SSTORE(key=0x1, value=0x6),
    ]
    tx_gas = [56000, 150000]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
