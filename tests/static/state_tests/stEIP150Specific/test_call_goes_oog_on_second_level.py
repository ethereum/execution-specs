"""
Ported from:
tests/static/state_tests/stEIP150Specific/CallGoesOOGOnSecondLevelFiller.json

callee code:
    gas
    push1 0x08
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xccc0159bd2ef7118b5e7b8d958e72237f02493fe
    push3 0x0493e0
    call
    push1 0x09
    sstore
    push1 0x01
    push1 0x0c
    sstore
    stop

contract code:
    gas
    push1 0x08
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x066f77b181e0e662e17d427c7320267adf2fd624
    push3 0x0927c0
    call
    push1 0x09
    sstore
    stop

callee_1 code:
    gas
    push1 0x08
    sstore
    push3 0x2fffff
    push1 0x00
    sha3
    pop
    gas
    push1 0x09
    sstore
    gas
    push1 0x0a
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
    ["tests/static/state_tests/stEIP150Specific/CallGoesOOGOnSecondLevelFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x3c6dca5471c6305d0642c6210d39d4613b5ea30b")
    callee = Address("0x066f77b181e0e662e17d427c7320267adf2fd624")
    callee_1 = Address("0xccc0159bd2ef7118b5e7b8d958e72237f02493fe")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xccc0159bd2ef7118b5e7b8d958e72237f02493fe] + Op.PUSH3[0x493e0]
        + Op.CALL + Op.PUSH1[0x9] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xc]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x66f77b181e0e662e17d427c7320267adf2fd624] + Op.PUSH3[0x927c0]
        + Op.CALL + Op.PUSH1[0x9] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH3[0x2fffff] + Op.PUSH1[0x0]
        + Op.SHA3 + Op.POP + Op.GAS + Op.PUSH1[0x9] + Op.SSTORE + Op.GAS
        + Op.PUSH1[0xa] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=2200000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
