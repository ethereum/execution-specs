"""
test_static_check_opcodes4

Ported from:
state_tests/stStaticCall/static_CheckOpcodes4Filler.json
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
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "",
]
TX_GAS = [50000, 335000]
TX_VALUE = [0, 100]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CheckOpcodes4Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="-g0-v0",
        ),
        pytest.param(
            0, 0, 1,
            id="-g0-v1",
        ),
        pytest.param(
            0, 1, 0,
            id="-g1-v0",
        ),
        pytest.param(
            0, 1, 1,
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
    """test_static_check_opcodes4"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { [[1]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[2]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) [[3]] (CALLER) [[4]] (CALLVALUE) [[5]] (ORIGIN) [[6]] (ADDRESS) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.STATICCALL(gas=0x186a0, address=0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.STATICCALL(gas=0x186a0, address=0x8fd6268252f0d331531601b40524719c7f681fe9, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x3, value=Op.CALLER)
        + Op.SSTORE(key=0x4, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x5, value=Op.ORIGIN)
        + Op.SSTORE(key=0x6, value=Op.ADDRESS) + Op.STOP,
        nonce=0,
        address=Address("0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:target:0x1000000000000000000000000000000000000000> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x1000000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x22, condition=Op.EQ(0xfaa10b404ab607779993c016cd5da73ae1f29d7e, Op.ORIGIN))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x28) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x4b, condition=Op.EQ(0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49, Op.CALLER))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x51) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x74, condition=Op.EQ(0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0, Op.ADDRESS))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x7a) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x8a, condition=Op.EQ(0x0, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x90) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0"),  # noqa: E501
    )
    # Source: lll
    # { (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:target:0x1000000000000000000000000000000000000000> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x1000000000000000000000000000000000000002> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x22, condition=Op.EQ(0xfaa10b404ab607779993c016cd5da73ae1f29d7e, Op.ORIGIN))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x28) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x4b, condition=Op.EQ(0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49, Op.CALLER))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x51) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x74, condition=Op.EQ(0x8fd6268252f0d331531601b40524719c7f681fe9, Op.ADDRESS))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x7a) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x8a, condition=Op.EQ(0x0, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x90) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0x8fd6268252f0d331531601b40524719c7f681fe9"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': 1, 'value': 0},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        target: Account(
                storage={
            1: 1,
            2: 1,
            3: 0xfaa10b404ab607779993c016cd5da73ae1f29d7e,
            5: 0xfaa10b404ab607779993c016cd5da73ae1f29d7e,
            6: 0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49,
        },
            ),
    },
        },
        {
            "indexes": {'data': -1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        target: Account(storage={}),
    },
        },
        {
            "indexes": {'data': -1, 'gas': 1, 'value': 1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        target: Account(
                storage={
            1: 1,
            2: 1,
            3: 0xfaa10b404ab607779993c016cd5da73ae1f29d7e,
            4: 100,
            5: 0xfaa10b404ab607779993c016cd5da73ae1f29d7e,
            6: 0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49,
        },
            ),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
