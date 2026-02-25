"""
Ported from:
tests/static/state_tests/stEIP150Specific/CallGoesOOGOnSecondLevel2Filler.json

contract code:
    gas
    push1 0x08
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xe1d370a0538366eaffbc9fcd571af7b1e80d377c
    push3 0x0927c0
    call
    push1 0x09
    sstore
    stop

callee code:
    gas
    push1 0x08
    sstore
    push3 0x2fffff
    push1 0x00
    sha3
    stop

callee_1 code:
    gas
    push1 0x08
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xbfb2b65e4ef26a144a185b32c7baf39ef8e40b4b
    push3 0x0927c0
    call
    push1 0x09
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
    ["tests/static/state_tests/stEIP150Specific/CallGoesOOGOnSecondLevel2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x171742e7809e3b571e899f0d4d9d35cd5deeacf1")
    callee = Address("0xbfb2b65e4ef26a144a185b32c7baf39ef8e40b4b")
    callee_1 = Address("0xe1d370a0538366eaffbc9fcd571af7b1e80d377c")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xe1d370a0538366eaffbc9fcd571af7b1e80d377c] + Op.PUSH3[0x927c0]
        + Op.CALL + Op.PUSH1[0x9] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH3[0x2fffff] + Op.PUSH1[0x0]
        + Op.SHA3 + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xbfb2b65e4ef26a144a185b32c7baf39ef8e40b4b] + Op.PUSH3[0x927c0]
        + Op.CALL + Op.PUSH1[0x9] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=160000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
