"""
Ported from:
tests/static/state_tests/stStaticCall/static_CheckOpcodes2Filler.json

callee code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x419fea0f3da444f3e6ae0c045f83dfe2b25f161b
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_1 code:
    push1 0x00
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0xef6a70e5546ca5339758b2f3b819780625c233c3
    push3 0x0186a0
    call
    push1 0x00
    mstore
    push1 0x01
    push1 0x01
    mstore
    push1 0x01
    push1 0x02
    mstore
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0x0e1fc3e8fa3dec60cc7fe8e5cf1a3bf2e23b8380
    push3 0x0186a0
    callcode
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    eq
    push1 0x38
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x3e
    ... (7 more instructions)

callee_3 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x66fa14f32eb562ef2161c2890c73dfe43779f135
    push3 0x0186a0
    call
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    eq
    push1 0x38
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x3e
    ... (7 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0186a0
    staticcall
    push1 0x01
    sstore
    stop

callee_4 code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_5 code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x4c9df443f25e673eac42a897aa8a234b84fb9bdd
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_6 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x7ea8b3e1880535d9ecf543c5af8637de220cd5fe
    push3 0x0186a0
    callcode
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    eq
    push1 0x38
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x3e
    ... (7 more instructions)

callee_7 code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x7493ed4fd2e14f56f1f1e3022b7c3873789b2254
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_8 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x58d6159788915466cc2bf8a6bc7284928707959b
    push3 0x0186a0
    delegatecall
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    eq
    push1 0x36
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x3c
    jump
    ... (6 more instructions)

callee_9 code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x17217475f7d93fbfac2586ae993da598daead310
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_CheckOpcodes2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_value",
    [
        ("0000000000000000000000004c9df443f25e673eac42a897aa8a234b84fb9bdd", 0),
        ("0000000000000000000000004c9df443f25e673eac42a897aa8a234b84fb9bdd", 100),
        ("00000000000000000000000017217475f7d93fbfac2586ae993da598daead310", 0),
        ("00000000000000000000000017217475f7d93fbfac2586ae993da598daead310", 100),
        ("0000000000000000000000007493ed4fd2e14f56f1f1e3022b7c3873789b2254", 0),
        ("0000000000000000000000007493ed4fd2e14f56f1f1e3022b7c3873789b2254", 100),
        ("000000000000000000000000419fea0f3da444f3e6ae0c045f83dfe2b25f161b", 0),
        ("000000000000000000000000419fea0f3da444f3e6ae0c045f83dfe2b25f161b", 100),
        ("000000000000000000000000991c2daacf958845c0a5e957b3e187238a093149", 0),
        ("000000000000000000000000991c2daacf958845c0a5e957b3e187238a093149", 100),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9'],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_opcodes2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c")
    callee = Address("0x0e1fc3e8fa3dec60cc7fe8e5cf1a3bf2e23b8380")
    callee_1 = Address("0x17217475f7d93fbfac2586ae993da598daead310")
    callee_2 = Address("0x419fea0f3da444f3e6ae0c045f83dfe2b25f161b")
    callee_3 = Address("0x4c9df443f25e673eac42a897aa8a234b84fb9bdd")
    callee_4 = Address("0x58d6159788915466cc2bf8a6bc7284928707959b")
    callee_5 = Address("0x66fa14f32eb562ef2161c2890c73dfe43779f135")
    callee_6 = Address("0x7493ed4fd2e14f56f1f1e3022b7c3873789b2254")
    callee_7 = Address("0x7ea8b3e1880535d9ecf543c5af8637de220cd5fe")
    callee_8 = Address("0x991c2daacf958845c0a5e957b3e187238a093149")
    callee_9 = Address("0xef6a70e5546ca5339758b2f3b819780625c233c3")

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
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x419fea0f3da444f3e6ae0c045f83dfe2b25f161b] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x419fea0f3da444f3e6ae0c045f83dfe2b25f161b] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x1] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH20[0xef6a70e5546ca5339758b2f3b819780625c233c3] + Op.PUSH3[0x186a0]
        + Op.CALL + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0xe1fc3e8fa3dec60cc7fe8e5cf1a3bf2e23b8380]
        + Op.PUSH3[0x186a0] + Op.CALLCODE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0x38] + Op.JUMPI + Op.PUSH1[0x2]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x3e] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x66fa14f32eb562ef2161c2890c73dfe43779f135]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0x38] + Op.JUMPI + Op.PUSH1[0x2]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x3e] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x186a0] + Op.STATICCALL
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x991c2daacf958845c0a5e957b3e187238a093149] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x4c9df443f25e673eac42a897aa8a234b84fb9bdd] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x66fa14f32eb562ef2161c2890c73dfe43779f135] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x7ea8b3e1880535d9ecf543c5af8637de220cd5fe]
        + Op.PUSH3[0x186a0] + Op.CALLCODE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0x38] + Op.JUMPI + Op.PUSH1[0x2]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x3e] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x7493ed4fd2e14f56f1f1e3022b7c3873789b2254] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x7493ed4fd2e14f56f1f1e3022b7c3873789b2254] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_8] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x58d6159788915466cc2bf8a6bc7284928707959b] + Op.PUSH3[0x186a0]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0x36] + Op.JUMPI + Op.PUSH1[0x2]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x3c] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_9] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x17217475f7d93fbfac2586ae993da598daead310] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0xef6a70e5546ca5339758b2f3b819780625c233c3] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x1] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=tx_data,
        gas_limit=335000,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
