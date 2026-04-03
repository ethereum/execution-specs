"""
Test_jump_bounds2.

Ported from:
state_tests/stMemoryStressTest/JUMP_Bounds2Filler.json
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
    ["state_tests/stMemoryStressTest/JUMP_Bounds2Filler.json"],
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
def test_jump_bounds2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_jump_bounds2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x31B5AF02B012484AE954B3A43943242EDE546A2E76FC0A6ACC17435107C385EB
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x63ffffffff5667ffffffffffffffff566fffffffffffffffffffffffffffffffff567fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff56  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0xFFFFFFFF)
        + Op.JUMP(pc=0xFFFFFFFFFFFFFFFF)
        + Op.JUMP(pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.JUMP(
            pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
        ),
        nonce=0,
        address=Address(0xDE573D26B8C4A55FD9DAA17E8F93347C269EE4F6),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFF)

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

    post = {
        target: Account(
            code=bytes.fromhex(
                "63ffffffff5667ffffffffffffffff566fffffffffffffffffffffffffffffffff567fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff56"  # noqa: E501
            ),
            balance=0,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
