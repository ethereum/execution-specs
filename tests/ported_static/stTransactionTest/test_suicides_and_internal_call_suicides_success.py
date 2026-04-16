"""
Test_suicides_and_internal_call_suicides_success.

Ported from:
state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesSuccessFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
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
        "state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesSuccessFiller.json"  # noqa: E501
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
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_suicides_and_internal_call_suicides_success(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_suicides_and_internal_call_suicides_success."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_0 = Address(0x0000000000000000000000000000000000000000)
    contract_1 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xABA9500)
    # Source: lll
    # {(SELFDESTRUCT 0x0000000000000000000000000000000000000001)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {(CALL (CALLDATALOAD 0) 0x0000000000000000000000000000000000000000 1 0 0 0 0) (SELFDESTRUCT 0)}  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=Op.CALLDATALOAD(offset=contract_0),
                address=contract_0,
                value=0x1,
                args_offset=contract_0,
                args_size=contract_0,
                ret_offset=contract_0,
                ret_size=contract_0,
            )
        )
        + Op.SELFDESTRUCT(address=contract_0)
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    0x0000000000000000000000000000000000000001
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0x0000000000000000000000000000000000000001): Account(
                    storage={}, balance=1
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0x55F0),
        Hash(0xAAF0),
    ]
    tx_gas = [150000]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
