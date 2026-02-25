"""
Ported from:
tests/static/state_tests/stStaticCall/static_Return50000_2Filler.json

callee code:
    push2 0xc34f
    calldataload
    push1 0x00
    mstore
    push1 0x01
    push1 0x00
    mload
    return
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xdf43bba207127b641624b20497fa07055f4a3939
    gas
    call
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_1 code:
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x3d
    jumpi
    push1 0x00
    push1 0x00
    push2 0xc350
    push1 0x00
    push20 0x0d08fb89197bd8f97c770ed75e28ed610a3016e9
    push2 0x061c
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x80
    mload
    ... (11 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_Return50000_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_return50000_2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40")
    contract = Address("0x9a8ca98b299a0220faad60948d01ce83ccc97831")
    callee = Address("0x0d08fb89197bd8f97c770ed75e28ed610a3016e9")
    callee_1 = Address("0xdf43bba207127b641624b20497fa07055f4a3939")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89250000,
    )

    pre[callee] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.PUSH2[0xc34f] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MLOAD + Op.RETURN + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdf43bba207127b641624b20497fa07055f4a3939]
        + Op.GAS + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x3d] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xc350] + Op.PUSH1[0x0]
        + Op.PUSH20[0xd08fb89197bd8f97c770ed75e28ed610a3016e9] + Op.PUSH2[0x61c]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x80]
        + Op.MLOAD + Op.ADD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474"
        ),
        to=contract,
        data=b"",
        gas_limit=15500000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
