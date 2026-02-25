"""
Ported from:
tests/static/state_tests/stStaticCall/static_Call1MB1024CalldepthFiller.json

callee_1 code:
    push1 0x01
    push1 0x00
    mload
    add
    push1 0x00
    mstore
    push2 0x0400
    push1 0x00
    mload
    lt
    push1 0x1b
    jumpi
    push1 0x01
    push1 0x40
    mstore
    push1 0x45
    jump
    jumpdest
    push1 0x00
    push1 0x00
    ... (11 more instructions)

callee_2 code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    sstore
    push2 0x0400
    push1 0x00
    sload
    lt
    push1 0x1b
    jumpi
    push1 0x01
    push1 0x02
    sstore
    push1 0x45
    jump
    jumpdest
    push1 0x00
    push1 0x00
    ... (11 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    gas
    call
    push1 0x00
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
    ["tests/static/state_tests/stStaticCall/static_Call1MB1024CalldepthFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000a79ae640e38871970f579f62237dfe2705068825",
        "000000000000000000000000583aa587d7d852a5b8448cc4160537d9bd12c889",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call1_mb1024_calldepth(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40")
    contract = Address("0xb16dbbe237612935e6611c3f5fb7d80eb0046801")
    callee = Address("0x2ab8257767339461506c0c67824cf17bc77b52ca")
    callee_1 = Address("0x583aa587d7d852a5b8448cc4160537d9bd12c889")
    callee_2 = Address("0xa79ae640e38871970f579f62237dfe2705068825")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=892500000000,
    )

    pre[callee] = Account(balance=0xfffffffffffff, nonce=0)
    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[callee_1] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH2[0x400] + Op.PUSH1[0x0] + Op.MLOAD + Op.LT
        + Op.PUSH1[0x1b] + Op.JUMPI + Op.PUSH1[0x1] + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH1[0x45] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH3[0xf4240] + Op.PUSH1[0x0]
        + Op.PUSH20[0x583aa587d7d852a5b8448cc4160537d9bd12c889] + Op.PUSH3[0xf55c8]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.PUSH1[0x20] + Op.MSTORE + Op.JUMPDEST
        + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH2[0x400] + Op.PUSH1[0x0] + Op.SLOAD + Op.LT
        + Op.PUSH1[0x1b] + Op.JUMPI + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SSTORE
        + Op.PUSH1[0x45] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH3[0xf4240] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa79ae640e38871970f579f62237dfe2705068825] + Op.PUSH3[0xf55c8]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.PUSH1[0x1] + Op.SSTORE + Op.JUMPDEST
        + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474"
        ),
        to=contract,
        data=tx_data,
        gas_limit=882500000000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
