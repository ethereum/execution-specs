"""
Test_dup_bounds.

Ported from:
state_tests/stMemoryStressTest/DUP_BoundsFiller.json
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
    ["state_tests/stMemoryStressTest/DUP_BoundsFiller.json"],
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
def test_dup_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_dup_bounds."""
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
    # 0x600080505063ffffffff80505067ffffffffffffffff8050506fffffffffffffffffffffffffffffffff8050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff805050600060008150505063ffffffff63ffffffff8150505067ffffffffffffffff67ffffffffffffffff815050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff815050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff81505050600060006000825050505063ffffffff63ffffffff63ffffffff825050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff82505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff82505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8250505050600060006000600083505050505063ffffffff63ffffffff63ffffffff63ffffffff83505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff8350505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff8350505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff835050505050600060006000600060008450505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff8450505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff845050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff845050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff84505050505050600060006000600060006000855050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff855050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff85505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff85505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8550505050505050600060006000600060006000600086505050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff86505050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff8650505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff8650505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff865050505050505050600060006000600060006000600060008750505050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff8750505050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff875050505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff875050505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff87  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.POP(Op.DUP1)
        + Op.POP
        + Op.PUSH4[0xFFFFFFFF]
        + Op.POP(Op.DUP1)
        + Op.POP
        + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
        + Op.POP(Op.DUP1)
        + Op.POP
        + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.POP(Op.DUP1)
        + Op.POP
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.POP(Op.DUP1)
        + Op.POP
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.DUP2)
        + Op.POP * 2
        + Op.PUSH4[0xFFFFFFFF] * 2
        + Op.POP(Op.DUP2)
        + Op.POP * 2
        + Op.PUSH8[0xFFFFFFFFFFFFFFFF] * 2
        + Op.POP(Op.DUP2)
        + Op.POP * 2
        + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF] * 2
        + Op.POP(Op.DUP2)
        + Op.POP * 2
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        * 2
        + Op.POP(Op.DUP2)
        + Op.POP * 2
        + Op.PUSH1[0x0] * 3
        + Op.POP(Op.DUP3)
        + Op.POP * 3
        + Op.PUSH4[0xFFFFFFFF] * 3
        + Op.POP(Op.DUP3)
        + Op.POP * 3
        + Op.PUSH8[0xFFFFFFFFFFFFFFFF] * 3
        + Op.POP(Op.DUP3)
        + Op.POP * 3
        + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF] * 3
        + Op.POP(Op.DUP3)
        + Op.POP * 3
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        * 3
        + Op.POP(Op.DUP3)
        + Op.POP * 3
        + Op.PUSH1[0x0] * 4
        + Op.POP(Op.DUP4)
        + Op.POP * 4
        + Op.PUSH4[0xFFFFFFFF] * 4
        + Op.POP(Op.DUP4)
        + Op.POP * 4
        + Op.PUSH8[0xFFFFFFFFFFFFFFFF] * 4
        + Op.POP(Op.DUP4)
        + Op.POP * 4
        + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF] * 4
        + Op.POP(Op.DUP4)
        + Op.POP * 4
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        * 4
        + Op.POP(Op.DUP4)
        + Op.POP * 4
        + Op.PUSH1[0x0] * 5
        + Op.POP(Op.DUP5)
        + Op.POP * 5
        + Op.PUSH4[0xFFFFFFFF] * 5
        + Op.POP(Op.DUP5)
        + Op.POP * 5
        + Op.PUSH8[0xFFFFFFFFFFFFFFFF] * 5
        + Op.POP(Op.DUP5)
        + Op.POP * 5
        + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF] * 5
        + Op.POP(Op.DUP5)
        + Op.POP * 5
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        * 5
        + Op.POP(Op.DUP5)
        + Op.POP * 5
        + Op.PUSH1[0x0] * 6
        + Op.POP(Op.DUP6)
        + Op.POP * 6
        + Op.PUSH4[0xFFFFFFFF] * 6
        + Op.POP(Op.DUP6)
        + Op.POP * 6
        + Op.PUSH8[0xFFFFFFFFFFFFFFFF] * 6
        + Op.POP(Op.DUP6)
        + Op.POP * 6
        + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF] * 6
        + Op.POP(Op.DUP6)
        + Op.POP * 6
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        * 6
        + Op.POP(Op.DUP6)
        + Op.POP * 6
        + Op.PUSH1[0x0] * 7
        + Op.POP(Op.DUP7)
        + Op.POP * 7
        + Op.PUSH4[0xFFFFFFFF] * 7
        + Op.POP(Op.DUP7)
        + Op.POP * 7
        + Op.PUSH8[0xFFFFFFFFFFFFFFFF] * 7
        + Op.POP(Op.DUP7)
        + Op.POP * 7
        + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF] * 7
        + Op.POP(Op.DUP7)
        + Op.POP * 7
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        * 7
        + Op.POP(Op.DUP7)
        + Op.POP * 7
        + Op.PUSH1[0x0] * 8
        + Op.POP(Op.DUP8)
        + Op.POP * 8
        + Op.PUSH4[0xFFFFFFFF] * 8
        + Op.POP(Op.DUP8)
        + Op.POP * 8
        + Op.PUSH8[0xFFFFFFFFFFFFFFFF] * 8
        + Op.POP(Op.DUP8)
        + Op.POP * 8
        + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF] * 8
        + Op.POP(Op.DUP8)
        + Op.POP * 8
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        * 8
        + Op.DUP8,
        nonce=0,
        address=Address(0xE860BD7BF0474923E526CBE86FA5B5F76AEE36ED),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFF)

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

    post = {target: Account(balance=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
