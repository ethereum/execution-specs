"""
Test_revert_opcode_direct_call.

Ported from:
state_tests/stRevertTest/RevertOpcodeDirectCallFiller.json
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
    ["state_tests/stRevertTest/RevertOpcodeDirectCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
def test_revert_opcode_direct_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_opcode_direct_call."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # {  [[10]] (CALL 60000 (CALLDATALOAD 0) 0 0 0 0 0)}
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0xA,
            value=Op.CALL(
                gas=0xEA60,
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
    addr_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xC)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.SSTORE(key=0x3, value=0xD)
        + Op.STOP,
        balance=1,
    )
    # Source: lll
    # { [[0]] (CALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] 14 }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0xC350,
                address=addr_2,
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
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_2: Account(storage={}),
                target: Account(storage={0: 0, 2: 14}, nonce=1),
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_2: Account(storage={}),
                target: Account(storage={}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(target, left_padding=True),
    ]
    tx_gas = [460000, 62912]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
