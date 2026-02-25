"""
Ported from:
tests/static/state_tests/stStaticCall/static_Call1024OOGFiller.json

callee code:
    push1 0x01
    push1 0x00
    mload
    add
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x42223ec7d9570a769becbe4beed7d885e01e6e37
    push2 0x0401
    push1 0x00
    mload
    div
    push1 0x01
    sub
    push2 0x2710
    gas
    sub
    ... (12 more instructions)

callee_1 code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x5eb006f1716196a0d072b390030a665386c48b9b
    push2 0x0401
    push1 0x00
    sload
    div
    push1 0x01
    sub
    push2 0x2710
    gas
    sub
    ... (13 more instructions)

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
    ["tests/static/state_tests/stStaticCall/static_Call1024OOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000005eb006f1716196a0d072b390030a665386c48b9b",
        "00000000000000000000000042223ec7d9570a769becbe4beed7d885e01e6e37",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call1024_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x42223ec7d9570a769becbe4beed7d885e01e6e37")
    callee_1 = Address("0x5eb006f1716196a0d072b390030a665386c48b9b")
    callee_2 = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[callee] = Account(
        balance=1024,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x42223ec7d9570a769becbe4beed7d885e01e6e37] + Op.PUSH2[0x401]
        + Op.PUSH1[0x0] + Op.MLOAD + Op.DIV + Op.PUSH1[0x1] + Op.SUB
        + Op.PUSH2[0x2710] + Op.GAS + Op.SUB + Op.MUL + Op.STATICCALL + Op.POP
        + Op.PUSH2[0x3e8] + Op.PUSH1[0x0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH1[0x20] + Op.MSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[callee_1] = Account(
        balance=1024,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x5eb006f1716196a0d072b390030a665386c48b9b] + Op.PUSH2[0x401]
        + Op.PUSH1[0x0] + Op.SLOAD + Op.DIV + Op.PUSH1[0x1] + Op.SUB
        + Op.PUSH2[0x2710] + Op.GAS + Op.SUB + Op.MUL + Op.STATICCALL + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH2[0x3e8] + Op.PUSH1[0x0] + Op.SLOAD + Op.MUL
        + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
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
    pre[callee_2] = Account(balance=7000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474"
        ),
        to=contract,
        data=tx_data,
        gas_limit=15720826,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
