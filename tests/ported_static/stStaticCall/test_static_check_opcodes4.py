"""
Test_static_check_opcodes4.

Ported from:
state_tests/stStaticCall/static_CheckOpcodes4Filler.json
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
    ["state_tests/stStaticCall/static_CheckOpcodes4Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-g0-v1",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="-g1-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_opcodes4(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_check_opcodes4."""
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
    # { [[1]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[2]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) [[3]] (CALLER) [[4]] (CALLVALUE) [[5]] (ORIGIN) [[6]] (ADDRESS) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0xB4B91C40F3E3A6E5576B0413572B88D535CEE7B0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0x8FD6268252F0D331531601B40524719C7F681FE9,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x3, value=Op.CALLER)
        + Op.SSTORE(key=0x4, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x5, value=Op.ORIGIN)
        + Op.SSTORE(key=0x6, value=Op.ADDRESS)
        + Op.STOP,
        nonce=0,
        address=Address(0x3350A62DDDDD0FF0E39CD82E2D185FE06B5FCF49),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:target:0x1000000000000000000000000000000000000000> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x1000000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x22,
            condition=Op.EQ(
                0xFAA10B404AB607779993C016CD5DA73AE1F29D7E, Op.ORIGIN
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x28)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x4B,
            condition=Op.EQ(
                0x3350A62DDDDD0FF0E39CD82E2D185FE06B5FCF49, Op.CALLER
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x51)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x74,
            condition=Op.EQ(
                0xB4B91C40F3E3A6E5576B0413572B88D535CEE7B0, Op.ADDRESS
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x7A)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x90)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address(0xB4B91C40F3E3A6E5576B0413572B88D535CEE7B0),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:target:0x1000000000000000000000000000000000000000> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x1000000000000000000000000000000000000002> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x22,
            condition=Op.EQ(
                0xFAA10B404AB607779993C016CD5DA73AE1F29D7E, Op.ORIGIN
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x28)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x4B,
            condition=Op.EQ(
                0x3350A62DDDDD0FF0E39CD82E2D185FE06B5FCF49, Op.CALLER
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x51)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x74,
            condition=Op.EQ(
                0x8FD6268252F0D331531601B40524719C7F681FE9, Op.ADDRESS
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x7A)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x90)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address(0x8FD6268252F0D331531601B40524719C7F681FE9),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(
                    storage={
                        1: 1,
                        2: 1,
                        3: 0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                        5: 0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                        6: 0x3350A62DDDDD0FF0E39CD82E2D185FE06B5FCF49,
                    },
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(storage={}),
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(
                    storage={
                        1: 1,
                        2: 1,
                        3: 0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                        4: 100,
                        5: 0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                        6: 0x3350A62DDDDD0FF0E39CD82E2D185FE06B5FCF49,
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [50000, 335000]
    tx_value = [0, 100]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
