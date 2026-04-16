"""
Account already has storage X. create -> in init code change that...

Ported from:
state_tests/stSStoreTest/sstore_changeFromExternalCallInInitCodeFiller.json
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
    [
        "state_tests/stSStoreTest/sstore_changeFromExternalCallInInitCodeFiller.json"  # noqa: E501
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
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8",
        ),
        pytest.param(
            9,
            0,
            0,
            id="d9",
        ),
        pytest.param(
            10,
            0,
            0,
            id="d10",
        ),
        pytest.param(
            11,
            0,
            0,
            id="d11",
        ),
        pytest.param(
            12,
            0,
            0,
            id="d12",
        ),
        pytest.param(
            13,
            0,
            0,
            id="d13",
        ),
        pytest.param(
            14,
            0,
            0,
            id="d14",
        ),
        pytest.param(
            15,
            0,
            0,
            id="d15",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_change_from_external_call_in_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Account already has storage X."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xBEA0000000000000000000000000000000000000)
    contract_1 = Address(0xDEA0000000000000000000000000000000000000)
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
    # { (SSTORE 1 0) (SSTORE 1 1) (SSTORE 0 1) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x0, value=0x1)
        + Op.STOP,
        storage={1: 1},
        nonce=0,
        address=Address(0xBEA0000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 1 [[1]] 0 [[2]] 1 [[2]] 0 [[3]] 1 [[3]] 0 [[4]] 1 [[4]] 0 [[5]] 1 [[5]] 0 [[6]] 1 [[6]] 0 [[7]] 1 [[7]] 0 [[8]] 1 [[8]] 0 [[9]] 1 [[9]] 0 [[10]] 1 [[10]] 0 [[11]] 1 [[11]] 0 [[12]] 1 [[12]] 0 [[13]] 1 [[13]] 0 [[14]] 1 [[14]] 0 [[15]] 1 [[15]] 0 [[16]] 1 [[16]] 0  [[1]] 1 }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x1)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.SSTORE(key=0x4, value=0x1)
        + Op.SSTORE(key=0x4, value=0x0)
        + Op.SSTORE(key=0x5, value=0x1)
        + Op.SSTORE(key=0x5, value=0x0)
        + Op.SSTORE(key=0x6, value=0x1)
        + Op.SSTORE(key=0x6, value=0x0)
        + Op.SSTORE(key=0x7, value=0x1)
        + Op.SSTORE(key=0x7, value=0x0)
        + Op.SSTORE(key=0x8, value=0x1)
        + Op.SSTORE(key=0x8, value=0x0)
        + Op.SSTORE(key=0x9, value=0x1)
        + Op.SSTORE(key=0x9, value=0x0)
        + Op.SSTORE(key=0xA, value=0x1)
        + Op.SSTORE(key=0xA, value=0x0)
        + Op.SSTORE(key=0xB, value=0x1)
        + Op.SSTORE(key=0xB, value=0x0)
        + Op.SSTORE(key=0xC, value=0x1)
        + Op.SSTORE(key=0xC, value=0x0)
        + Op.SSTORE(key=0xD, value=0x1)
        + Op.SSTORE(key=0xD, value=0x0)
        + Op.SSTORE(key=0xE, value=0x1)
        + Op.SSTORE(key=0xE, value=0x0)
        + Op.SSTORE(key=0xF, value=0x1)
        + Op.SSTORE(key=0xF, value=0x0)
        + Op.SSTORE(key=0x10, value=0x1)
        + Op.SSTORE(key=0x10, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xDEA0000000000000000000000000000000000000),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1, 3], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 1, 1: 1}, nonce=0)},
        },
        {
            "indexes": {
                "data": [2, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16],
                "gas": 0,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={0: 0, 1: 1}, nonce=0),
                Address(
                    0x6602CFC925BE62BF18470598A98F72812A1EBEF2
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [4], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={0: 0, 1: 1}, nonce=0),
                compute_create_address(address=sender, nonce=0): Account(
                    storage={0: 1, 1: 1}, nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [5, 7], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={0: 0, 1: 1}, nonce=0),
                Address(0x0F446E1BD7A5DA68B5E3A305C7030E3AA8EFC293): Account(
                    storage={0: 1, 1: 1}, nonce=1
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.CALL(
            gas=0x186A0,
            address=contract_0,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x25]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.CALL(
            gas=0x186A0,
            address=contract_0,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x25]
        + Op.CODECOPY(dest_offset=0x0, offset=0x18, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.REVERT(offset=0x0, size=0x0)
        + Op.STOP * 2
        + Op.INVALID
        + Op.CALL(
            gas=0x186A0,
            address=contract_0,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x25]
        + Op.CODECOPY(dest_offset=0x0, offset=0x38, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.POP(
            Op.CALL(
                gas=0x30D40,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.STOP * 2
        + Op.INVALID
        + Op.CALL(
            gas=0x186A0,
            address=contract_0,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.CALLCODE(
            gas=0x186A0,
            address=contract_0,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x25]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.CALLCODE(
            gas=0x186A0,
            address=contract_0,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x25]
        + Op.CODECOPY(dest_offset=0x0, offset=0x18, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.REVERT(offset=0x0, size=0x0)
        + Op.STOP * 2
        + Op.INVALID
        + Op.CALLCODE(
            gas=0x186A0,
            address=contract_0,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x25]
        + Op.CODECOPY(dest_offset=0x0, offset=0x38, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.POP(
            Op.CALL(
                gas=0x30D40,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.STOP * 2
        + Op.INVALID
        + Op.CALLCODE(
            gas=0x186A0,
            address=contract_0,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.DELEGATECALL(
            gas=0x186A0,
            address=contract_0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x23]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.DELEGATECALL(
            gas=0x186A0,
            address=contract_0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x23]
        + Op.CODECOPY(dest_offset=0x0, offset=0x18, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.REVERT(offset=0x0, size=0x0)
        + Op.STOP * 2
        + Op.INVALID
        + Op.DELEGATECALL(
            gas=0x186A0,
            address=contract_0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x23]
        + Op.CODECOPY(dest_offset=0x0, offset=0x38, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.POP(
            Op.CALL(
                gas=0x30D40,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.STOP * 2
        + Op.INVALID
        + Op.DELEGATECALL(
            gas=0x186A0,
            address=contract_0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.STATICCALL(
            gas=0x186A0,
            address=contract_0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x23]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.STATICCALL(
            gas=0x186A0,
            address=contract_0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x23]
        + Op.CODECOPY(dest_offset=0x0, offset=0x18, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.REVERT(offset=0x0, size=0x0)
        + Op.STOP * 2
        + Op.INVALID
        + Op.STATICCALL(
            gas=0x186A0,
            address=contract_0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x23]
        + Op.CODECOPY(dest_offset=0x0, offset=0x38, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.POP(
            Op.CALL(
                gas=0x30D40,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.STOP * 2
        + Op.INVALID
        + Op.STATICCALL(
            gas=0x186A0,
            address=contract_0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    ]
    tx_gas = [200000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
