"""
Test_create_e_contract_create_ne_contract_in_init_oog_tr.

Ported from:
state_tests/stCreateTest/CREATE_EContractCreateNEContractInInitOOG_TrFiller.json
"""

import pytest
from execution_testing import (
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
    [
        "state_tests/stCreateTest/CREATE_EContractCreateNEContractInInitOOG_TrFiller.json"  # noqa: E501
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_e_contract_create_ne_contract_in_init_oog_tr(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_create_e_contract_create_ne_contract_in_init_oog_tr."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # {[[1]]12}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0xC) + Op.STOP,
        balance=0xE8D4A51000,
        nonce=0,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={1: 12}),
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=2
                ),
                compute_create_address(
                    address=compute_create_address(address=sender, nonce=0),
                    nonce=0,
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={1: 0}),
                compute_create_address(
                    address=sender, nonce=0
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=compute_create_address(address=sender, nonce=0),
                    nonce=0,
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.POP(
            Op.CALL(
                gas=0xEA60,
                address=contract_0,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x64600C6000556000526005601BF3)
        + Op.CREATE(value=0x0, offset=0x12, size=0xE),
    ]
    tx_gas = [160000, 60000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
