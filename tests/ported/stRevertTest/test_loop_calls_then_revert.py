"""
Ported from:
tests/static/state_tests/stRevertTest/LoopCallsThenRevertFiller.json

contract code:
    jumpdest
    push1 0x01
    push1 0x00
    sload
    sub
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xc47bcbf49dd735566cfde927821e938d5b33014c
    push2 0xc350
    call
    pop
    push1 0x00
    sload
    push1 0x00
    jumpi

callee code:
    push1 0x00
    sload
    push1 0x01
    add
    push1 0x00
    sstore
    stop
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
    ["tests/static/state_tests/stRevertTest/LoopCallsThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_loop_calls_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x0347aff20d9d3c574e18f3b17dc267ddcd2d75ca")
    callee = Address("0xc47bcbf49dd735566cfde927821e938d5b33014c")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.SUB
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc47bcbf49dd735566cfde927821e938d5b33014c] + Op.PUSH2[0xc350]
        + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x0] + Op.JUMPI
    ),
        storage={0x0: 0x352},
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=10000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
