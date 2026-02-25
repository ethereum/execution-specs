"""
Ported from:
tests/static/state_tests/stStaticCall/static_Call50000Filler.json

callee code:
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x3e
    jumpi
    push1 0x00
    push1 0x00
    push2 0xc350
    push1 0x00
    push20 0x7efd7e4e34d1783f5d86b7862a37b3bbbd13deb8
    push3 0x0186a0
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x80
    mload
    ... (11 more instructions)

callee_1 code:
    push1 0x00
    sload
    push1 0x00
    mstore
    stop

callee_2 code:
    push1 0x00
    sload
    push1 0x00
    sstore
    stop

callee_3 code:
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x3e
    jumpi
    push1 0x00
    push1 0x00
    push2 0xc350
    push1 0x00
    push20 0x6d440cd3e818056e21914c856e3712f4186b06c8
    push3 0x0186a0
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x80
    mload
    ... (11 more instructions)

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
    ["tests/static/state_tests/stStaticCall/static_Call50000Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000002e396fd4f6f2799d61f534b43175f5344c65ecac",
        "000000000000000000000000b00a8701f877b1152cd955e957fcbaf51a15f55f",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call50000(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x2e396fd4f6f2799d61f534b43175f5344c65ecac")
    callee_1 = Address("0x6d440cd3e818056e21914c856e3712f4186b06c8")
    callee_2 = Address("0x7efd7e4e34d1783f5d86b7862a37b3bbbd13deb8")
    callee_3 = Address("0xb00a8701f877b1152cd955e957fcbaf51a15f55f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000,
    )

    pre[callee] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x3e] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xc350] + Op.PUSH1[0x0]
        + Op.PUSH20[0x7efd7e4e34d1783f5d86b7862a37b3bbbd13deb8] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x80]
        + Op.MLOAD + Op.ADD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[callee_1] = Account(
        balance=7000,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.STOP,
        storage={0x0: 0x1},
    )
    pre[callee_2] = Account(
        balance=7000,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
        storage={0x0: 0x1},
    )
    pre[callee_3] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x3e] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xc350] + Op.PUSH1[0x0]
        + Op.PUSH20[0x6d440cd3e818056e21914c856e3712f4186b06c8] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x80]
        + Op.MLOAD + Op.ADD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x20] + Op.SSTORE
        + Op.STOP
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

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474"
        ),
        to=contract,
        data=tx_data,
        gas_limit=90000000000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
