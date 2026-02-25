"""
Ported from:
tests/static/state_tests/stRevertTest/LoopCallsDepthThenRevert3Filler.json

contract code:
    push2 0x03fe
    push1 0x00
    sload
    eq
    push1 0x3f
    jumpi
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xa000000000000000000000000000000000000000
    gas
    call
    ... (17 more instructions)
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRevertTest/LoopCallsDepthThenRevert3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_loop_calls_depth_then_revert3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xa000000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[contract] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH2[0x3fe] + Op.PUSH1[0x0] + Op.SLOAD + Op.EQ + Op.PUSH1[0x3f]
        + Op.JUMPI + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xa000000000000000000000000000000000000000]
        + Op.GAS + Op.CALL + Op.POP + Op.PUSH2[0x41a] + Op.PUSH1[0x0] + Op.SLOAD
        + Op.LT + Op.PUSH1[0x53] + Op.JUMPI + Op.JUMPDEST + Op.PUSH7[0x600060006002f0]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x7] + Op.PUSH1[0x19] + Op.PUSH1[0x3]
        + Op.CREATE + Op.POP + Op.JUMPDEST
    ),
    )
    pre[sender] = Account(balance=0x13426172c74d822b878fe800000000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=9214364837600034817,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
