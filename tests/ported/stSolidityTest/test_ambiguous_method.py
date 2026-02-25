"""
Ported from:
tests/static/state_tests/stSolidityTest/AmbiguousMethodFiller.json

contract code:
    push1 0x00
    calldataload
    push1 0xe0
    push1 0x02
    exp
    swap1
    div
    dup1
    push4 0xc0406226
    eq
    push1 0x15
    jumpi
    stop
    jumpdest
    push1 0x1b
    push1 0x21
    jump
    jumpdest
    push1 0x00
    push1 0x00
    ... (9 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/AmbiguousMethodFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ambiguous_method(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x73c241c3bc4fdf83b6ff3ae73735fddf7c9d711d")
    contract = Address("0x235c9320b0f4d30204334c1ddb008dfe1d75b1b9")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xe0] + Op.PUSH1[0x2] + Op.EXP
        + Op.SWAP1 + Op.DIV + Op.DUP1 + Op.PUSH4[0xc0406226] + Op.EQ + Op.PUSH1[0x15]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x1b] + Op.PUSH1[0x21] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH2[0x14f] + Op.PUSH1[0x0] + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.JUMP
    ),
    )
    pre[sender] = Account(balance=0x12a05f200, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xa9ae12cb2700c0214f86b9796881bc03a1fd5605d0e76d2da2ca592e62d53e52"
        ),
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=300000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
