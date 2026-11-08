"""
Test_revert_opcode_calls.

Ported from:
state_tests/stRevertTest/RevertOpcodeCallsFiller.json
@manually-enhanced: Do not overwrite. Gas bumped fork-conditionally
to cover EIP-8037 state-gas spill into regular gas; pre-EIP-8037
behavior unchanged. The d3 call chain ends in a fresh SSTORE-set in
the outermost (transaction) frame; with an empty state-gas reservoir
that set's state gas spills into regular gas, so the success path
(g=0) runs out at the final `SSTORE` unless the outer budget absorbs
the spill. Lift `tx_gas[0]` by one fresh-set SSTORE state cost via
`fork.oog_budget_lift`, which is exactly 0 pre-EIP-8037 and tracks
the parameter. g=1 (the OoG case) keeps the original budget.

"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertOpcodeCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0",
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3-g0",
        ),
        pytest.param(
            3,
            1,
            0,
            id="d3-g1",
        ),
    ],
)
def test_revert_opcode_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_opcode_calls."""
    # EIP-8037 gas bumps: original values for pre-EIP-8037 forks.
    inner_call_gas = 50000
    inner_call_gas_2 = 100000
    inner_call_gas_3 = 260000
    if fork.is_eip_enabled(8037):
        inner_call_gas = 1000000
        inner_call_gas_2 = 1000000
        inner_call_gas_3 = 1300000

    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # {  [[10]] (CALL 260000 (CALLDATALOAD 0) 0 0 0 0 0)}
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0xA,
            value=Op.CALL(
                gas=inner_call_gas_3,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=1,
    )
    # Source: lll
    # { [[1]] 12 (REVERT 0 1) [[3]] 13 }
    addr_6 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xC)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.SSTORE(key=0x3, value=0xD)
        + Op.STOP,
        balance=1,
    )
    # Source: lll
    # { [[4]] (CALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[5]] 14 }  # noqa: E501
    addr_5 = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x4,
            value=Op.CALL(
                gas=inner_call_gas,
                address=addr_6,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x5, value=0xE)
        + Op.STOP,
        balance=1,
    )
    # Source: lll
    # { [[0]] (CALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] 14 }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=inner_call_gas,
                address=addr_6,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0xE)
        + Op.STOP,
        balance=1,
    )
    # Source: lll
    # { [[0]] (DELEGATECALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[2]] 14 }  # noqa: E501
    addr_3 = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=inner_call_gas,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0xE)
        + Op.STOP,
        balance=1,
    )
    # Source: lll
    # { [[0]] (CALLCODE 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] 14 }  # noqa: E501
    addr_2 = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=inner_call_gas,
                address=addr_6,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0xE)
        + Op.STOP,
        balance=1,
    )
    # Source: lll
    # { [[0]] (CALL 100000 <contract:0xb3305374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] 14 }  # noqa: E501
    addr_4 = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=inner_call_gas_2,
                address=addr_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0xE)
        + Op.STOP,
        balance=1,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                target: Account(storage={10: 1}),
                addr: Account(storage={0: 0, 2: 14}, nonce=1),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                addr: Account(storage={}),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                target: Account(storage={10: 1}),
                addr_2: Account(storage={0: 0, 2: 14}, nonce=1),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                addr_2: Account(storage={}),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                target: Account(storage={10: 1}),
                addr_3: Account(storage={0: 0, 2: 14}, nonce=1),
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                addr_3: Account(storage={}),
            },
        },
        {
            "indexes": {"data": 3, "gas": [0], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                target: Account(storage={10: 1}),
                addr_4: Account(storage={0: 1, 2: 14}, nonce=1),
                addr_5: Account(storage={4: 0, 5: 14}, nonce=1),
            },
        },
        {
            "indexes": {"data": 3, "gas": [1], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                target: Account(storage={10: 0}),
                addr_4: Account(storage={0: 0, 2: 0}, nonce=1),
                addr_5: Account(storage={4: 0, 5: 0}, nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
        Hash(addr_4, left_padding=True),
    ]
    # The g=0 success path bottoms out on a fresh SSTORE-set in the
    # transaction frame whose EIP-8037 state gas spills (empty
    # reservoir). Lift the outer budget by that spilled state cost so
    # the chain still completes on Amsterdam; 0 pre-EIP-8037.
    g0_lift = fork.oog_budget_lift(sstores_before_oog=1)
    tx_gas = [460000 + g0_lift, 83622]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
