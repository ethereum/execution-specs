"""
Ported from:
tests/static/state_tests/stStaticCall/static_Call50000_identity2Filler.json

callee code:
    push1 0x2a
    push1 0x01
    mstore
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x30
    jumpi
    push2 0xc350
    push1 0x01
    push2 0xc350
    push1 0x00
    push1 0x04
    push2 0x061c
    staticcall
    push1 0x00
    mstore
    ... (18 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    callvalue
    push1 0x00
    calldataload
    gas
    call
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_1 code:
    push1 0x2a
    push1 0x01
    mstore
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x30
    jumpi
    push2 0xc350
    push1 0x01
    push2 0xc350
    push1 0x00
    push1 0x04
    push2 0x061c
    staticcall
    push1 0x00
    sstore
    ... (18 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_Call50000_identity2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000cfb4c99d22928822feffa77a1a6de64042e48dd3",
        "000000000000000000000000b02bd8691a1a4f5fd4432b5b17c68dde3013fc35",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call50000_identity2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0xb02bd8691a1a4f5fd4432b5b17c68dde3013fc35")
    callee_1 = Address("0xcfb4c99d22928822feffa77a1a6de64042e48dd3")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=8925000000,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[callee] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.PUSH1[0x2a] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.PUSH2[0xc350]
        + Op.PUSH1[0x80] + Op.MLOAD + Op.LT + Op.ISZERO + Op.PUSH1[0x30] + Op.JUMPI
        + Op.PUSH2[0xc350] + Op.PUSH1[0x1] + Op.PUSH2[0xc350] + Op.PUSH1[0x0]
        + Op.PUSH1[0x4] + Op.PUSH2[0x61c] + Op.STATICCALL + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x5] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x80]
        + Op.MLOAD + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x1] + Op.MLOAD
        + Op.PUSH1[0x40] + Op.MSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.PUSH1[0x2a] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.PUSH2[0xc350]
        + Op.PUSH1[0x80] + Op.MLOAD + Op.LT + Op.ISZERO + Op.PUSH1[0x30] + Op.JUMPI
        + Op.PUSH2[0xc350] + Op.PUSH1[0x1] + Op.PUSH2[0xc350] + Op.PUSH1[0x0]
        + Op.PUSH1[0x4] + Op.PUSH2[0x61c] + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x5] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x80]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x1] + Op.MLOAD
        + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474"
        ),
        to=contract,
        data=tx_data,
        gas_limit=882500000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
