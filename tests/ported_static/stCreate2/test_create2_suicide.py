"""
CREATE2 suicide with/without value, CREATE2 suicide to itself   +  this...

Ported from:
state_tests/stCreate2/CREATE2_SuicideFiller.json
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
    ["state_tests/stCreate2/CREATE2_SuicideFiller.json"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """CREATE2 suicide with/without value, CREATE2 suicide to itself   + ..."""
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
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    0x0000000000000000000000000000000000000001
                ): Account.NONEXISTENT,
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=2
                ),
                Address(
                    0x5649527A8464A86CAE579719D347065F6EB27279
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [2, 3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0x0000000000000000000000000000000000000001): Account(
                    balance=1
                ),
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=2
                ),
                Address(
                    0x5649527A8464A86CAE579719D347065F6EB27279
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [4, 5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=2
                ),
                Address(
                    0x6CD0E5133771823DA00D4CB545EC8CDAB0E38203
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [6, 7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    balance=9, nonce=2
                ),
                Address(
                    0x6CD0E5133771823DA00D4CB545EC8CDAB0E38203
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [8, 9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=2
                ),
                Address(0x5649527A8464A86CAE579719D347065F6EB27279): Account(
                    code=bytes.fromhex("6001ff")
                ),
            },
        },
        {
            "indexes": {"data": [10, 11], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=2
                ),
                Address(0x6CD0E5133771823DA00D4CB545EC8CDAB0E38203): Account(
                    code=bytes.fromhex("30ff")
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.MSTORE(offset=0x0, value=0x6001FF)
        + Op.CREATE2(value=0x0, offset=0x1D, size=0x3, salt=0x0)
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x626001FF6000526003601DF3)
        + Op.POP(Op.CREATE2(value=0x0, offset=0x14, size=0xC, salt=0x0))
        + Op.CALL(
            gas=0x249F0,
            address=0x5649527A8464A86CAE579719D347065F6EB27279,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x6001FF)
        + Op.CREATE2(value=0x1, offset=0x1D, size=0x3, salt=0x0)
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x626001FF6000526003601DF3)
        + Op.POP(Op.CREATE2(value=0x1, offset=0x14, size=0xC, salt=0x0))
        + Op.CALL(
            gas=0x249F0,
            address=0x5649527A8464A86CAE579719D347065F6EB27279,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x30FF)
        + Op.CREATE2(value=0x0, offset=0x1E, size=0x2, salt=0x0)
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x6130FF6000526002601EF3)
        + Op.POP(Op.CREATE2(value=0x0, offset=0x15, size=0xB, salt=0x0))
        + Op.CALL(
            gas=0x249F0,
            address=0x6CD0E5133771823DA00D4CB545EC8CDAB0E38203,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x30FF)
        + Op.CREATE2(value=0x1, offset=0x1E, size=0x2, salt=0x0)
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x6130FF6000526002601EF3)
        + Op.POP(Op.CREATE2(value=0x1, offset=0x15, size=0xB, salt=0x0))
        + Op.CALL(
            gas=0x249F0,
            address=0x6CD0E5133771823DA00D4CB545EC8CDAB0E38203,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x626001FF6000526003601DF3)
        + Op.POP(Op.CREATE2(value=0x0, offset=0x14, size=0xC, salt=0x0))
        + Op.STATICCALL(
            gas=0x249F0,
            address=0x5649527A8464A86CAE579719D347065F6EB27279,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x626001FF6000526003601DF3)
        + Op.POP(Op.CREATE2(value=0x1, offset=0x14, size=0xC, salt=0x0))
        + Op.STATICCALL(
            gas=0x249F0,
            address=0x5649527A8464A86CAE579719D347065F6EB27279,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x6130FF6000526002601EF3)
        + Op.POP(Op.CREATE2(value=0x0, offset=0x15, size=0xB, salt=0x0))
        + Op.STATICCALL(
            gas=0x249F0,
            address=0x6CD0E5133771823DA00D4CB545EC8CDAB0E38203,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x6130FF6000526002601EF3)
        + Op.POP(Op.CREATE2(value=0x1, offset=0x15, size=0xB, salt=0x0))
        + Op.STATICCALL(
            gas=0x249F0,
            address=0x6CD0E5133771823DA00D4CB545EC8CDAB0E38203,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    ]
    tx_gas = [600000]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
