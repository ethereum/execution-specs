"""
Test_delegatecall_bounds.

Ported from:
state_tests/stMemoryStressTest/DELEGATECALL_BoundsFiller.json
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
    ["state_tests/stMemoryStressTest/DELEGATECALL_BoundsFiller.json"],
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
def test_delegatecall_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_delegatecall_bounds."""
    sender = pre.fund_eoa(amount=2**128 - 1)

    # Source: lll
    # { (SSTORE 0 (ADD 1 (SLOAD 0))) }
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.STOP,
    )
    # Source: lll
    # {(DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xfffffff 0 0xfffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffff 0 0xffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xfffffff 0 0xfffffff 0) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffff 0 0xffffffff 0)  (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffff 0 0xffffffffffffffff 0) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffff 0) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xfffffff 0xfffffff 0xfffffff 0xfffffff)  }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr,
                args_offset=0x0,
                args_size=0xFFFFFFF,
                ret_offset=0x0,
                ret_size=0xFFFFFFF,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr,
                args_offset=0x0,
                args_size=0xFFFFFFFF,
                ret_offset=0x0,
                ret_size=0xFFFFFFFF,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr,
                args_offset=0xFFFFFFF,
                args_size=0x0,
                ret_offset=0xFFFFFFF,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr,
                args_offset=0xFFFFFFFF,
                args_size=0x0,
                ret_offset=0xFFFFFFFF,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr,
                args_offset=0xFFFFFFFFFFFFFFFF,
                args_size=0x0,
                ret_offset=0xFFFFFFFFFFFFFFFF,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr,
                args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                args_size=0x0,
                ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr,
                args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                args_size=0x0,
                ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ret_size=0x0,
            )
        )
        + Op.DELEGATECALL(
            gas=0x7FFFFFFFFFFFFFF,
            address=addr,
            args_offset=0xFFFFFFF,
            args_size=0xFFFFFFF,
            ret_offset=0xFFFFFFF,
            ret_size=0xFFFFFFF,
        )
        + Op.STOP,
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(storage={0: 0}, balance=0)}

    state_test(pre=pre, post=post, tx=tx)
