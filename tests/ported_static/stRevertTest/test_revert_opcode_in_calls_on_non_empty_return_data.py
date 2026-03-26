"""
This test checks that the returndata buffer is changed when a subcall REVERTs.  In each test case, a non-empty returndata buffer is set up, and then calls into a contract that REVERTs.

Ported from:
state_tests/stRevertTest/RevertOpcodeInCallsOnNonEmptyReturnDataFiller.json
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
    "000000000000000000000000e73611b5b479b30c93ac377aeb3bfb199764f3c3",
    "000000000000000000000000c9da6cd8413f64323f12cd44c99671f280f15e1c",
    "000000000000000000000000f20ccaf271beaa36e7cf4c9ced2867fac9558f14",
    "0000000000000000000000006bacdfa8216dbb2a09819f8739e57ae3574c9fff",
]
TX_GAS = [860000, 28000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertOpcodeInCallsOnNonEmptyReturnDataFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0-g0",
        ),
        pytest.param(
            0, 1, 0,
            id="d0-g1",
        ),
        pytest.param(
            1, 0, 0,
            id="d1-g0",
        ),
        pytest.param(
            1, 1, 0,
            id="d1-g1",
        ),
        pytest.param(
            2, 0, 0,
            id="d2-g0",
        ),
        pytest.param(
            2, 1, 0,
            id="d2-g1",
        ),
        pytest.param(
            3, 0, 0,
            id="d3-g0",
        ),
        pytest.param(
            3, 1, 0,
            id="d3-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_in_calls_on_non_empty_return_data(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """This test checks that the returndata buffer is changed when a subca..."""
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
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[10]] (CALL 260000 (CALLDATALOAD 0) 0 0 0 0 0)}
    target = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x0, address=0x127eaf7e31d691a8393b7a2f84a6e94372190c01, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0xa, value=Op.CALL(gas=0x3f7a0, address=Op.CALLDATALOAD(offset=0x0), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        storage={10: 255},
        balance=1,
        nonce=0,
        address=Address("0x172a8f572404293aa810685dfdc6f740c300cc4b"),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[0]] (CALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] (RETURNDATASIZE) }
    addr_0xb0005374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x0, address=0x127eaf7e31d691a8393b7a2f84a6e94372190c01, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x0, value=Op.CALL(gas=0xc350, address=0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0xe73611b5b479b30c93ac377aeb3bfb199764f3c3"),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[0]] (CALLCODE 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] (RETURNDATASIZE) }
    addr_0xb1005374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x0, address=0x127eaf7e31d691a8393b7a2f84a6e94372190c01, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x0, value=Op.CALLCODE(gas=0xc350, address=0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0xc9da6cd8413f64323f12cd44c99671f280f15e1c"),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[0]] (DELEGATECALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[2]] (RETURNDATASIZE) }
    addr_0xb2005374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x0, address=0x127eaf7e31d691a8393b7a2f84a6e94372190c01, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x0, value=Op.DELEGATECALL(gas=0xc350, address=0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0xf20ccaf271beaa36e7cf4c9ced2867fac9558f14"),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[0]] (CALL 100000 <contract:0xb3305374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] (RETURNDATASIZE) }
    addr_0xb3005374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x0, address=0x127eaf7e31d691a8393b7a2f84a6e94372190c01, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x0, value=Op.CALL(gas=0x186a0, address=0xea519c47889074e6378b0d83747f2c3ea0b9cbc9, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0x6bacdfa8216dbb2a09819f8739e57ae3574c9fff"),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[4]] (CALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[5]] (RETURNDATASIZE) }
    addr_0xb3305374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x0, address=0x127eaf7e31d691a8393b7a2f84a6e94372190c01, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x4, value=Op.CALL(gas=0xc350, address=0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x5, value=Op.RETURNDATASIZE) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0xea519c47889074e6378b0d83747f2c3ea0b9cbc9"),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 12 (REVERT 0 1) [[3]] 13 }
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xc) + Op.REVERT(offset=0x0, size=0x1)
        + Op.SSTORE(key=0x3, value=0xd) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b"),  # noqa: E501
    )
    # Source: lll
    # { [1] 12 (RETURN 0 64) }
    addr_0xffff5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0xc) + Op.RETURN(offset=0x0, size=0x40)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0x127eaf7e31d691a8393b7a2f84a6e94372190c01"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
        target: Account(storage={10: 1}),
        addr_0xb0005374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={2: 1}, nonce=0),
    },
        },
        {
            "indexes": {'data': 0, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
        addr_0xb0005374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
    },
        },
        {
            "indexes": {'data': 1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
        target: Account(storage={10: 1}),
        addr_0xb1005374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={2: 1}, nonce=0),
    },
        },
        {
            "indexes": {'data': 1, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
        addr_0xb1005374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
    },
        },
        {
            "indexes": {'data': 2, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
        target: Account(storage={10: 1}),
        addr_0xb2005374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={2: 1}, nonce=0),
    },
        },
        {
            "indexes": {'data': 2, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
        addr_0xb2005374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
    },
        },
        {
            "indexes": {'data': 3, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
        target: Account(storage={10: 1}),
        addr_0xb3005374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={0: 1}, nonce=0),
        addr_0xb3305374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={5: 1}, nonce=0),
    },
        },
        {
            "indexes": {'data': 3, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
        target: Account(storage={10: 255}),
        addr_0xb3005374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={0: 0}, nonce=0),
        addr_0xb3305374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={5: 0}, nonce=0),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
