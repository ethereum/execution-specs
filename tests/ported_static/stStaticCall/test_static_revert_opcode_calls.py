"""
Test_static_revert_opcode_calls.

Ported from:
state_tests/stStaticCall/static_RevertOpcodeCallsFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_RevertOpcodeCallsFiller.json"],
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
def test_static_revert_opcode_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_revert_opcode_calls."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { (REVERT 0 1) }
    addr = pre.deploy_contract(
        code=Op.REVERT(offset=0x0, size=0x1) + Op.STOP,
        balance=1,
    )
    # Source: lll
    # {   [[0]] (STATICCALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[1]] (RETURNDATASIZE)}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0xC350,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.STOP,
        balance=1,
    )

    tx_data = [
        Bytes(""),
    ]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
    )

    post = {target: Account(storage={1: 1})}

    state_test(pre=pre, post=post, tx=tx)
