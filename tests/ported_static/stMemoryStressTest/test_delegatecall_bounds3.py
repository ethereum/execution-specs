"""
Test_delegatecall_bounds3.

Ported from:
state_tests/stMemoryStressTest/DELEGATECALL_Bounds3Filler.json
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stMemoryStressTest/DELEGATECALL_Bounds3Filler.json"],
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
        pytest.param(
            0,
            2,
            0,
            id="-g2",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_delegatecall_bounds3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_delegatecall_bounds3."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x50EADFB1030587AB3A993A6ECC073041FC3B45E119DAA31A13D78C7E209631A5
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: lll
    # { (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffff 0 0xffffffffffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffff 0xffffffffffffffff 0xffffffffffffffff 0xffffffffffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                args_offset=0x0,
                args_size=0xFFFFFFFFFFFFFFFF,
                ret_offset=0x0,
                ret_size=0xFFFFFFFFFFFFFFFF,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                args_offset=0x0,
                args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ret_offset=0x0,
                ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                args_offset=0x0,
                args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ret_offset=0x0,
                ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                args_offset=0xFFFFFFFFFFFFFFFF,
                args_size=0xFFFFFFFFFFFFFFFF,
                ret_offset=0xFFFFFFFFFFFFFFFF,
                ret_size=0xFFFFFFFFFFFFFFFF,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            )
        )
        + Op.DELEGATECALL(
            gas=0x7FFFFFFFFFFFFFF,
            address=0x849F53126ADE5F72469029537296F2B6644D4D41,
            args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x5A6CC254B318BB5F7539FCC10CFB01C517154C5C),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 (ADD 1 (SLOAD 0))) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.STOP,
        nonce=0,
        address=Address(0x849F53126ADE5F72469029537296F2B6644D4D41),  # noqa: E501
    )
    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 1000000, 16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(storage={0: 0}, balance=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
