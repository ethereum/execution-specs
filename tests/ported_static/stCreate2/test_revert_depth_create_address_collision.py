"""
Copy of this test for CREATE2.

Ported from:
state_tests/stCreate2/RevertDepthCreateAddressCollisionFiller.json
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
    ["state_tests/stCreate2/RevertDepthCreateAddressCollisionFiller.json"],
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
def test_revert_depth_create_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Copy of this test for CREATE2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x3E180B1862F9D158ABB5E519A6D8605540C23682)
    contract_1 = Address(0xB000000000000000000000000000000000000000)
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

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [[2]] 8 (CREATE2 0 0 0 0) [[3]] 12}
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0x8)
        + Op.POP(Op.CREATE2(value=0x0, offset=0x0, size=0x0, salt=0x0))
        + Op.SSTORE(key=0x3, value=0xC)
        + Op.STOP,
        nonce=0,
        address=Address(0xB000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { [[0]] 1 [[1]] (CALL (CALLDATALOAD 0) 0xb000000000000000000000000000000000000000 0 0 0 0 0) [[4]] 12 }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=Op.CALLDATALOAD(offset=0x0),
                address=0xB000000000000000000000000000000000000000,
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
        address=Address(0x3E180B1862F9D158ABB5E519A6D8605540C23682),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={0: 1, 1: 1, 4: 12}, nonce=54),
                contract_1: Account(storage={2: 8, 3: 12}),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={0: 1, 4: 12}, nonce=54),
                contract_1: Account(storage={}),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={},
                    code=bytes.fromhex(
                        "60016000556000600060006000600073b000000000000000000000000000000000000000600035f1600155600c60045500"  # noqa: E501
                    ),
                    balance=5,
                    nonce=54,
                ),
                contract_1: Account(storage={}),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={},
                    code=bytes.fromhex(
                        "60016000556000600060006000600073b000000000000000000000000000000000000000600035f1600155600c60045500"  # noqa: E501
                    ),
                    nonce=54,
                ),
                contract_1: Account(storage={}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0xEA60),
        Hash(0x1EA60),
    ]
    tx_gas = [110000, 170000]
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
