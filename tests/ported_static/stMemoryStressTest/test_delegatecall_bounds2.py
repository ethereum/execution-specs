"""
Test_delegatecall_bounds2.

Ported from:
state_tests/stMemoryStressTest/DELEGATECALL_Bounds2Filler.json
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
    ["state_tests/stMemoryStressTest/DELEGATECALL_Bounds2Filler.json"],
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
@pytest.mark.pre_alloc_mutable
def test_delegatecall_bounds2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_delegatecall_bounds2."""
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
    # { (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffff 0xffffffff 0xffffffff 0xffffffff) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=0x7FFFFFFFFFFFFFF,
            address=0x849F53126ADE5F72469029537296F2B6644D4D41,
            args_offset=0xFFFFFFFF,
            args_size=0xFFFFFFFF,
            ret_offset=0xFFFFFFFF,
            ret_size=0xFFFFFFFF,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x7B7E1FED40D6CB2420C7F2718725BADB76616D4D),  # noqa: E501
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
    tx_gas = [150000, 16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(storage={}, balance=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
