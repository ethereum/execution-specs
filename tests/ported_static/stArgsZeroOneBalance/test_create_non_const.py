"""
Test_create_non_const.

Ported from:
state_tests/stArgsZeroOneBalance/createNonConstFiller.yml
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
    ["state_tests/stArgsZeroOneBalance/createNonConstFiller.yml"],
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
@pytest.mark.pre_alloc_mutable
def test_create_non_const(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_create_non_const."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { [[ 0 ]] (CREATE (BALANCE 0x095e7baea6a6c7c4c2dfeb977efac326af552d87) (BALANCE 0x095e7baea6a6c7c4c2dfeb977efac326af552d87) (BALANCE 0x095e7baea6a6c7c4c2dfeb977efac326af552d87)) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CREATE(
                value=Op.BALANCE(
                    address=0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87
                ),
                offset=Op.BALANCE(
                    address=0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87
                ),
                size=Op.BALANCE(
                    address=0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87
                ),
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={0: 0xD2571607E241ECF590ED94B12D87C94BABE36DB6},
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": -1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={0: 0xD2571607E241ECF590ED94B12D87C94BABE36DB6},
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
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
