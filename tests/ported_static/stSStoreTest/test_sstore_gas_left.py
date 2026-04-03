"""
Checks EIP-1706/EIP-2200 out of gas requirement for non-mutating SSTOREs.

Ported from:
state_tests/stSStoreTest/sstore_gasLeftFiller.json
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
    ["state_tests/stSStoreTest/sstore_gasLeftFiller.json"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Checks EIP-1706/EIP-2200 out of gas requirement for non-mutating..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
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
    # { [[1]] 1 }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        storage={1: 1},
        nonce=0,
        address=Address(0xB0409D84AB61455CB8BEC14B94F635146AB55613),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 1 }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x4092B3905CFEA2485EA53222F41EB26E67587802),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1, 3, 4, 6, 7], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {addr_2: Account(storage={1: 0})},
        },
        {
            "indexes": {"data": [8, 2, 5], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {addr_2: Account(storage={1: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.JUMPI(
            pc=0x4B,
            condition=Op.ISZERO(
                Op.CALL(
                    gas=0x901,
                    address=addr,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                )
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=0x7530,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.STOP,
        Op.JUMPI(
            pc=0x4B,
            condition=Op.ISZERO(
                Op.CALL(
                    gas=0x902,
                    address=addr,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                )
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=0x7530,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.STOP,
        Op.JUMPI(
            pc=0x4B,
            condition=Op.ISZERO(
                Op.CALL(
                    gas=0x903,
                    address=addr,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                )
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=0x7530,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.STOP,
        Op.SSTORE(key=0x1, value=0x1)
        + Op.JUMPI(
            pc=0x50,
            condition=Op.ISZERO(
                Op.CALLCODE(
                    gas=0x901,
                    address=addr,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                )
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=0x7530,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.STOP,
        Op.SSTORE(key=0x1, value=0x1)
        + Op.JUMPI(
            pc=0x50,
            condition=Op.ISZERO(
                Op.CALLCODE(
                    gas=0x902,
                    address=addr,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                )
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=0x7530,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.STOP,
        Op.SSTORE(key=0x1, value=0x1)
        + Op.JUMPI(
            pc=0x50,
            condition=Op.ISZERO(
                Op.CALLCODE(
                    gas=0x903,
                    address=addr,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                )
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=0x7530,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.STOP,
        Op.SSTORE(key=0x1, value=0x1)
        + Op.JUMPI(
            pc=0x4E,
            condition=Op.ISZERO(
                Op.DELEGATECALL(
                    gas=0x901,
                    address=addr,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                )
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=0x7530,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.STOP,
        Op.SSTORE(key=0x1, value=0x1)
        + Op.JUMPI(
            pc=0x4E,
            condition=Op.ISZERO(
                Op.DELEGATECALL(
                    gas=0x902,
                    address=addr,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                )
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=0x7530,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.STOP,
        Op.SSTORE(key=0x1, value=0x1)
        + Op.JUMPI(
            pc=0x4E,
            condition=Op.ISZERO(
                Op.DELEGATECALL(
                    gas=0x903,
                    address=addr,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                )
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=0x7530,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.STOP,
    ]
    tx_gas = [200000]
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
