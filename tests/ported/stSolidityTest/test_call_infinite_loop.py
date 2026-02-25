"""
Ported from:
tests/static/state_tests/stSolidityTest/CallInfiniteLoopFiller.json

contract code:
    push1 0x00
    calldataload
    push1 0xe0
    push1 0x02
    exp
    swap1
    div
    dup1
    push4 0x296df0df
    eq
    push1 0x29
    jumpi
    dup1
    push4 0x4893d88a
    eq
    push1 0x35
    jumpi
    dup1
    push4 0x981a3165
    eq
    ... (49 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/CallInfiniteLoopFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_infinite_loop(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = Address("0x01a87dcc756f6a6bd9e586598a5c1a44a1c6d945")
    contract = Address("0xf9b9ccb6160ce3574df5d096ca9fd12ba81d97ee")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x1dcd6500, nonce=0)
    pre[coinbase] = Account(balance=0, nonce=1)
    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xe0] + Op.PUSH1[0x2] + Op.EXP
        + Op.SWAP1 + Op.DIV + Op.DUP1 + Op.PUSH4[0x296df0df] + Op.EQ + Op.PUSH1[0x29]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0x4893d88a] + Op.EQ + Op.PUSH1[0x35]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0x981a3165] + Op.EQ + Op.PUSH1[0x41]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x2f] + Op.PUSH1[0x4d] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x3b] + Op.PUSH1[0x62] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x47] + Op.PUSH1[0x5a]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN
        + Op.JUMPDEST + Op.JUMPDEST + Op.PUSH1[0x1] + Op.ISZERO + Op.PUSH1[0x58]
        + Op.JUMPI + Op.PUSH1[0x4e] + Op.JUMP + Op.JUMPDEST + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x60] + Op.PUSH1[0x62] + Op.JUMP + Op.JUMPDEST + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x68] + Op.PUSH1[0x5a] + Op.JUMP + Op.JUMPDEST
        + Op.JUMP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x96c07046493ec8728482079ab999d2994420d9cf4d3491dfd06871b106d9d87b"
        ),
        to=contract,
        data=bytes.fromhex("296df0df"),
        gas_limit=300000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
