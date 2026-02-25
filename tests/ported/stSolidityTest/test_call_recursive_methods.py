"""
Ported from:
tests/static/state_tests/stSolidityTest/CallRecursiveMethodsFiller.json

contract code:
    push29 0x0100000000000000000000000000000000000000000000000000000000
    push1 0x00
    calldataload
    div
    push4 0x296df0df
    dup2
    eq
    push1 0x41
    jumpi
    dup1
    push4 0x4893d88a
    eq
    push1 0x4d
    jumpi
    dup1
    push4 0x981a3165
    eq
    push1 0x59
    jumpi
    stop
    ... (46 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/CallRecursiveMethodsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_recursive_methods(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = Address("0x73c241c3bc4fdf83b6ff3ae73735fddf7c9d711d")
    contract = Address("0xc7c7851c7f3291bed1039bb4ffa166c290a605a9")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x12a05f200, nonce=0)
    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0x296df0df] + Op.DUP2
        + Op.EQ + Op.PUSH1[0x41] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0x4893d88a] + Op.EQ
        + Op.PUSH1[0x4d] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0x981a3165] + Op.EQ
        + Op.PUSH1[0x59] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x47]
        + Op.PUSH1[0x65] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x53] + Op.PUSH1[0x7a] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x5f] + Op.PUSH1[0x72] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.ISZERO + Op.PUSH1[0x70] + Op.JUMPI + Op.PUSH1[0x66] + Op.JUMP
        + Op.JUMPDEST + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x78] + Op.PUSH1[0x7a]
        + Op.JUMP + Op.JUMPDEST + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x80]
        + Op.PUSH1[0x72] + Op.JUMP + Op.JUMPDEST + Op.JUMP
    ),
    )
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        secret_key=Hash(
            "0xa9ae12cb2700c0214f86b9796881bc03a1fd5605d0e76d2da2ca592e62d53e52"
        ),
        to=contract,
        data=bytes.fromhex("981a3165"),
        gas_limit=60000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
