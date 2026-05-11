"""
Test_revert_depth_create_oog.

Ported from:
state_tests/stRevertTest/RevertDepthCreateOOGFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
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
    ["state_tests/stRevertTest/RevertDepthCreateOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="d0-g0-v1",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="d0-g1-v1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0-v0",
        ),
        pytest.param(
            1,
            0,
            1,
            id="d1-g0-v1",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1-v0",
        ),
        pytest.param(
            1,
            1,
            1,
            id="d1-g1-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_depth_create_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_depth_create_oog."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xA000000000000000000000000000000000000000)
    contract_1 = Address(0xB000000000000000000000000000000000000000)
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
    # { [[2]] 8 (CREATE 0 0 0) [[3]] 12}
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0x8)
        + Op.POP(Op.CREATE(value=0x0, offset=0x0, size=0x0))
        + Op.SSTORE(key=0x3, value=0xC)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { [[0]] 1 [[1]] (CALL (CALLDATALOAD 0) 0xb000000000000000000000000000000000000000 0 0 0 0 0) [[4]] 12 }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=Op.CALLDATALOAD(offset=0x0),
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x4, value=0xC)
        + Op.STOP,
        balance=5,
        nonce=54,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=contract_1, nonce=0): Account(
                    nonce=1
                ),
                contract_0: Account(storage={0: 1, 1: 1, 4: 12}),
                contract_1: Account(storage={2: 8, 3: 12}),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(
                    address=contract_1, nonce=0
                ): Account.NONEXISTENT,
                contract_0: Account(storage={0: 1, 4: 12}),
                contract_1: Account(storage={}),
            },
        },
        {
            "indexes": {"data": [0, 1], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(
                    address=contract_1, nonce=0
                ): Account.NONEXISTENT,
                contract_0: Account(storage={}),
                contract_1: Account(storage={}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0xEA60),
        Hash(0x1EA60),
    ]
    tx_gas = [110000, 180000]
    tx_value = [1, 0]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
