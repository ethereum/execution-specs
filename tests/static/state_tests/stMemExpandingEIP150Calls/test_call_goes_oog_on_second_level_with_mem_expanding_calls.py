"""
Ported from:
tests/static/state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevelWithMemExpandingCallsFiller.json

callee code:
    gas
    push1 0x08
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    create
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    create
    pop
    gas
    push1 0x09
    sstore
    gas
    push1 0x0a
    sstore

callee_1 code:
    gas
    push1 0x08
    sstore
    push1 0xff
    push1 0xff
    push1 0xff
    push1 0xff
    push1 0x00
    push20 0x2ef686162bebf2542147767d5be471976860cceb
    push3 0x0927c0
    call
    push1 0x09
    sstore

contract code:
    gas
    push1 0x08
    sstore
    push1 0xff
    push1 0xff
    push1 0xff
    push1 0xff
    push1 0x00
    push20 0xa27e20572430916b3d6772b27329cc460224904d
    push3 0x0927c0
    call
    push1 0x09
    sstore
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
    ["tests/static/state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevelWithMemExpandingCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x823066fb511f07f5e49cbd8ca9874e4bc6ee9e65")
    contract = Address("0xaf229807016a538dfcdab92a53337de38178d40f")
    callee = Address("0x2ef686162bebf2542147767d5be471976860cceb")
    callee_1 = Address("0xa27e20572430916b3d6772b27329cc460224904d")

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
        + Op.PUSH1[0x0] + Op.CREATE + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CREATE + Op.POP + Op.GAS + Op.PUSH1[0x9] + Op.SSTORE
        + Op.GAS + Op.PUSH1[0xa] + Op.SSTORE
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0xff] + Op.PUSH1[0xff]
        + Op.PUSH1[0xff] + Op.PUSH1[0xff] + Op.PUSH1[0x0]
        + Op.PUSH20[0x2ef686162bebf2542147767d5be471976860cceb] + Op.PUSH3[0x927c0]
        + Op.CALL + Op.PUSH1[0x9] + Op.SSTORE
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0xff] + Op.PUSH1[0xff]
        + Op.PUSH1[0xff] + Op.PUSH1[0xff] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa27e20572430916b3d6772b27329cc460224904d] + Op.PUSH3[0x927c0]
        + Op.CALL + Op.PUSH1[0x9] + Op.SSTORE
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x8d19f2b0d2f5689c1771fbca70476ca6e877a81ee15c3733de87fae38e5abcef"
        ),
        to=contract,
        data=b"",
        gas_limit=220000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
