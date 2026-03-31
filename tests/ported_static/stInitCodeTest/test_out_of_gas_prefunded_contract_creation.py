"""
Test_out_of_gas_prefunded_contract_creation.

Ported from:
state_tests/stInitCodeTest/OutOfGasPrefundedContractCreationFiller.json
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


@pytest.mark.ported_from(
    [
        "state_tests/stInitCodeTest/OutOfGasPrefundedContractCreationFiller.json"  # noqa: E501
    ],
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
        pytest.param(
            0,
            2,
            0,
            id="-g2",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_out_of_gas_prefunded_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_out_of_gas_prefunded_contract_creation."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x6295EE1B4F6DD65047762F924ECD367C17EABF8F)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    pre[sender] = Account(balance=0xF424000)
    # Source: hex
    # 0x
    contract_0 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0x6295EE1B4F6DD65047762F924ECD367C17EABF8F),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": [0, 1], "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(balance=1),
            },
        },
        {
            "indexes": {"data": -1, "gas": [2], "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(balance=2),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.PUSH1[0x9]
        + Op.CODECOPY(dest_offset=0x0, offset=0x11, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x1]
        + Op.POP(Op.CREATE)
        + Op.STOP * 2
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=0x112233)
        + Op.STOP * 2,
    ]
    tx_gas = [154000, 65000, 95000]
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
