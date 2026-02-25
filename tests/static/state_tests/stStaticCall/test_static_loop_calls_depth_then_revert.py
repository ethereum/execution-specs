"""
Ported from:
tests/static/state_tests/stStaticCall/static_LoopCallsDepthThenRevertFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x15dc6ad6aa4b45c8c5f8658596f0be95f4fb77fd
    push3 0x0186a0
    gas
    sub
    call
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x8ac26ad64561031be35e49c24ee18c6e43c21795
    gas
    staticcall
    stop

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x77c35f69d9f67cc9c06c803eb2c0aca9c2a746e6
    gas
    staticcall
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
    ["tests/static/state_tests/stStaticCall/static_LoopCallsDepthThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_loop_calls_depth_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x15dc6ad6aa4b45c8c5f8658596f0be95f4fb77fd")
    callee = Address("0x77c35f69d9f67cc9c06c803eb2c0aca9c2a746e6")
    callee_1 = Address("0x8ac26ad64561031be35e49c24ee18c6e43c21795")

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
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x15dc6ad6aa4b45c8c5f8658596f0be95f4fb77fd]
        + Op.PUSH3[0x186a0] + Op.GAS + Op.SUB + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x8ac26ad64561031be35e49c24ee18c6e43c21795] + Op.GAS
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x77c35f69d9f67cc9c06c803eb2c0aca9c2a746e6] + Op.GAS
        + Op.STATICCALL + Op.STOP
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
