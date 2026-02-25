"""
Ported from:
tests/static/state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToEmpty_OOGRevert_ParisFiller.json

callee_1 code:
    push20 0x76fae819612a29489a1a43208613d8f8557b8898
    selfdestruct
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x888748026558f849c1b2433ea5e1daf1444dfc60
    push2 0xc350
    call
    pop
    push1 0x0c
    push1 0x02
    sstore
    push1 0x0c
    push1 0x03
    sstore
    push1 0x0c
    push1 0x04
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
    ["tests/static/state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToEmpty_OOGRevert_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_suicide_to_empty_oog_revert_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0xa2e25f47a24c66cfef22d3304777a22d6dd7ad4a")
    callee = Address("0x76fae819612a29489a1a43208613d8f8557b8898")
    callee_1 = Address("0x888748026558f849c1b2433ea5e1daf1444dfc60")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(balance=10, nonce=0)
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH20[0x76fae819612a29489a1a43208613d8f8557b8898] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x888748026558f849c1b2433ea5e1daf1444dfc60]
        + Op.PUSH2[0xc350] + Op.CALL + Op.POP + Op.PUSH1[0xc] + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x4] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=75000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
